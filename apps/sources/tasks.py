from __future__ import annotations

import hashlib
import logging
from urllib.parse import urlparse

from automation.adapters.contracts import CrawlContext, DiscoveredItem, FetchResult, SourceAdapter
from automation.adapters.registry import AdapterNotRegisteredLookupError, get_adapter
from automation.http.client import SafeHttpRequest, fetch_url_with_retries
from automation.pipeline.persistence import persist_parsed_call
from automation.pipeline.validation import is_portal_source_category
from django.conf import settings
from django.utils import timezone

from apps.ingestion.models import CrawlItem, CrawlRun
from apps.sources.locks import CrawlLock
from apps.sources.models import Source
from apps.sources.scheduler import due_sources, scheduler_can_run, scheduler_max_due_sources
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="sources.schedule_due_sources")
def schedule_due_sources() -> int:
    if not scheduler_can_run():
        return 0

    queued = 0
    for source in due_sources()[: scheduler_max_due_sources()]:
        crawl_source.delay(source.id)
        queued += 1
    return queued


@shared_task(name="sources.crawl_source")
def crawl_source(source_id: int) -> str:
    source = Source.objects.get(id=source_id)

    try:
        get_adapter(source.adapter_key)
    except AdapterNotRegisteredLookupError:
        logger.warning("No adapter registered for %s (source_id=%s), skipping.", source.adapter_key, source_id)
        return f"unsupported_adapter:{source.adapter_key}"

    lock = CrawlLock(source_id=source.id)
    if not lock.acquire():
        return "locked"

    run = CrawlRun.objects.create(
        source=source,
        trigger_type=CrawlRun.TriggerType.SCHEDULE,
        status=CrawlRun.Status.RUNNING,
        started_at=timezone.now(),
        config_version=source.config_version,
    )
    try:
        persisted_count = _crawl_source(source, run)
        _finish_run(run, status=CrawlRun.Status.COMPLETED)
        source.last_success_at = timezone.now()
        source.consecutive_failures = 0
        source.save(update_fields=["last_success_at", "consecutive_failures", "updated_at"])
        return f"persisted:{persisted_count}"
    except Exception as exc:
        run.error_code = exc.__class__.__name__
        run.error_summary = str(exc)[:500]
        _finish_run(run, status=CrawlRun.Status.FAILED)
        source.last_failure_at = timezone.now()
        source.consecutive_failures += 1
        source.save(update_fields=["last_failure_at", "consecutive_failures", "updated_at"])
        raise
    finally:
        lock.release()


def _crawl_source(source: Source, run: CrawlRun) -> int:
    adapter = get_adapter(source.adapter_key)
    context = CrawlContext(
        source_key=source.source_key or str(source.id),
        source_url=source.listing_url,
        adapter_key=source.adapter_key,
        config_version=source.config_version,
        settings=source.config_json,
    )
    persisted_count = 0

    for item in adapter.discover(context):
        try:
            persisted_count += _process_discovered_item(
                adapter=adapter,
                context=context,
                source=source,
                run=run,
                item=item,
                allow_detail_discovery=True,
            )
        except Exception:
            # Item failure already recorded in CrawlItem; continue with remaining items.
            logger.exception(
                "Item failed during crawl (source=%s url=%s), continuing.",
                source.source_key,
                item.normalized_url,
            )

    return persisted_count


def _process_discovered_item(
    *,
    adapter: SourceAdapter,
    context: CrawlContext,
    source: Source,
    run: CrawlRun,
    item: DiscoveredItem,
    allow_detail_discovery: bool,
) -> int:
    run.discovered_count += 1
    crawl_item = CrawlItem.objects.create(
        crawl_run=run,
        source_url=item.source_url,
        normalized_url=item.normalized_url,
        external_id=item.external_id,
        content_hash=item.content_hash,
        raw_metadata_json=dict(item.metadata),
    )
    try:
        response = fetch_url_with_retries(_safe_http_request_for(source=source, url=item.normalized_url))
        fetched_at = timezone.now()
        content_hash = item.content_hash or hashlib.sha256(response.body).hexdigest()
        crawl_item.status = CrawlItem.Status.FETCHED
        crawl_item.attempt_count += 1
        crawl_item.http_status = response.status_code
        crawl_item.content_hash = content_hash
        crawl_item.save(update_fields=["status", "attempt_count", "http_status", "content_hash", "updated_at"])
        run.fetched_count += 1
        _increment_http_status(run, response.status_code)

        fetch_result = FetchResult(
            item=item,
            final_url=response.final_url,
            status_code=response.status_code,
            content_type=response.content_type,
            body_text=response.body.decode("utf-8", errors="replace"),
            fetched_at=fetched_at,
            content_hash=content_hash,
            headers=response.headers,
            evidence_excerpt=response.body[:500].decode("utf-8", errors="replace"),
        )
        detail_items = _discover_detail_items(adapter=adapter, fetch_result=fetch_result, context=context)
        if allow_detail_discovery and detail_items:
            crawl_item.raw_metadata_json = dict(crawl_item.raw_metadata_json) | {"detail_count": len(detail_items)}
            crawl_item.save(update_fields=["raw_metadata_json", "updated_at"])
            return sum(
                _process_discovered_item(
                    adapter=adapter,
                    context=context,
                    source=source,
                    run=run,
                    item=detail_item,
                    allow_detail_discovery=False,
                )
                for detail_item in detail_items
            )
        if allow_detail_discovery and _is_portal_listing(context=context, item=item):
            crawl_item.raw_metadata_json = dict(crawl_item.raw_metadata_json) | {
                "detail_count": 0,
                "skipped_reason": "no_detail_links",
            }
            crawl_item.save(update_fields=["raw_metadata_json", "updated_at"])
            return 0

        parsed_call = adapter.parse(fetch_result, context)
        persisted = persist_parsed_call(
            source=source,
            parsed_call=parsed_call,
            fetched_at=fetched_at,
            content_hash=content_hash,
            parser_version=adapter.parser_version,
        )
        crawl_item.status = CrawlItem.Status.PARSED if persisted.created else CrawlItem.Status.DUPLICATE
        crawl_item.parser_version = adapter.parser_version
        crawl_item.grant_call = persisted.grant_call
        crawl_item.save(update_fields=["status", "parser_version", "grant_call", "updated_at"])
        if persisted.created:
            run.created_count += 1
        else:
            run.updated_count += 1
            run.duplicate_count += 1
        if persisted.review_created:
            run.review_count += 1
        return 1
    except Exception as exc:
        crawl_item.status = CrawlItem.Status.FAILED
        crawl_item.error_code = exc.__class__.__name__
        crawl_item.save(update_fields=["status", "error_code", "updated_at"])
        run.failed_count += 1
        raise  # re-raise so _crawl_source can log and continue with next item


def _discover_detail_items(
    *,
    adapter: object,
    fetch_result: FetchResult,
    context: CrawlContext,
) -> tuple[DiscoveredItem, ...]:
    discover_from_fetch = getattr(adapter, "discover_from_fetch", None)
    if not callable(discover_from_fetch):
        return ()
    return tuple(discover_from_fetch(fetch_result, context))


def _is_portal_listing(*, context: CrawlContext, item: DiscoveredItem) -> bool:
    source_category = str(context.settings.get("source_category", ""))
    return is_portal_source_category(source_category) and item.metadata.get("kind") != "detail"


def _allowed_hosts_for(source: Source) -> frozenset[str]:
    hosts = {parsed.hostname for parsed in (urlparse(source.base_url), urlparse(source.listing_url)) if parsed.hostname}
    hosts_with_www_variants = set(hosts)
    for host in hosts:
        if host.startswith("www."):
            hosts_with_www_variants.add(host.removeprefix("www."))
        else:
            hosts_with_www_variants.add(f"www.{host}")
    return frozenset(hosts_with_www_variants)


def _safe_http_request_for(*, source: Source, url: str) -> SafeHttpRequest:
    config = source.config_json if isinstance(source.config_json, dict) else {}
    robots_txt = config.get("robots_txt")
    return SafeHttpRequest(
        url=url,
        allowed_hosts=_allowed_hosts_for(source),
        user_agent=str(config.get("user_agent") or "HibeRotaBot/1.0"),
        contact_email=getattr(settings, "SECURITY_CONTACT_EMAIL", "security@example.invalid"),
        timeout_seconds=float(config.get("timeout_seconds") or 10),
        max_redirects=int(config.get("max_redirects") or 3),
        max_response_bytes=int(config.get("max_response_bytes") or 2_000_000),
        min_request_interval_seconds=float(config.get("min_request_interval_seconds") or 1),
        robots_txt=robots_txt if isinstance(robots_txt, str) and robots_txt else None,
    )


def _increment_http_status(run: CrawlRun, status_code: int) -> None:
    summary = dict(run.http_status_summary)
    key = str(status_code)
    summary[key] = int(summary.get(key, 0)) + 1
    run.http_status_summary = summary


def _finish_run(run: CrawlRun, *, status: str) -> None:
    run.status = status
    run.finished_at = timezone.now()
    run.save(
        update_fields=[
            "status",
            "finished_at",
            "discovered_count",
            "fetched_count",
            "created_count",
            "updated_count",
            "review_count",
            "duplicate_count",
            "failed_count",
            "http_status_summary",
            "error_code",
            "error_summary",
            "updated_at",
        ]
    )
