from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.sources.models import Source


def due_sources() -> list[Source]:
    now = timezone.now()
    sources = Source.objects.filter(status=Source.Status.ACTIVE).select_related("institution", "institution__country")
    allowlist = _scheduler_allowlist()
    if allowlist:
        sources = sources.filter(source_key__in=allowlist)
    return sorted(
        [source for source in sources if _source_is_due(source=source, now=now)],
        key=_source_priority_key,
    )


def scheduler_can_run() -> bool:
    if not getattr(settings, "SOURCE_SCHEDULER_ENABLED", True):
        return False
    if getattr(settings, "SOURCE_SCHEDULER_ROLLBACK_PAUSED", False):
        return False
    return bool(_scheduler_allowlist()) or not getattr(settings, "SOURCE_SCHEDULER_REQUIRE_ALLOWLIST", False)


def scheduler_max_due_sources() -> int:
    value = int(getattr(settings, "SOURCE_SCHEDULER_MAX_DUE_SOURCES", 5))
    return max(value, 0)


def _scheduler_allowlist() -> tuple[str, ...]:
    configured = getattr(settings, "SOURCE_SCHEDULER_ALLOWLIST", ())
    if isinstance(configured, str):
        return tuple(item.strip() for item in configured.split(",") if item.strip())
    return tuple(str(item).strip() for item in configured if str(item).strip())


def _source_is_due(*, source: Source, now: datetime) -> bool:
    interval = timedelta(minutes=source.crawl_interval_minutes)
    attempts = [item for item in (source.last_success_at, source.last_failure_at) if item is not None]
    last_attempt_at = max(attempts) if attempts else None
    return last_attempt_at is None or last_attempt_at <= now - interval


def _source_priority_key(source: Source) -> tuple[int, int, str]:
    country = source.institution.country
    if country.code == "TR":
        region_rank = 0
    elif country.is_europe or country.code == "EU":
        region_rank = 1
    else:
        region_rank = 2
    return region_rank, _catalog_priority(source), source.source_key or str(source.id)


def _catalog_priority(source: Source) -> int:
    raw_priority = source.config_json.get("priority", 99)
    try:
        return int(raw_priority)
    except (TypeError, ValueError):
        return 99
