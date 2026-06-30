from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.sources.models import Source


def due_sources() -> list[Source]:
    now = timezone.now()
    sources = Source.objects.filter(status=Source.Status.ACTIVE)
    allowlist = _scheduler_allowlist()
    if allowlist:
        sources = sources.filter(source_key__in=allowlist)
    return [source for source in sources if _source_is_due(source=source, now=now)]


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
