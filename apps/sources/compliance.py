from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse

from automation.http.client import (
    HostRateLimiter,
    SafeHttpError,
    SafeHttpRequest,
    fetch_url_with_retries,
    is_robots_allowed,
)
from django.utils import timezone

from apps.sources.models import Source

ROBOTS_USER_AGENT = "HibeRotaBot/1.0"
ROBOTS_CONTACT_EMAIL = "security@hiberota.com"


@dataclass(frozen=True, slots=True)
class RobotsCheckResult:
    source_id: int
    source_key: str
    robots_url: str
    status: str
    checked_at: datetime
    error: str = ""


def check_source_robots(
    source: Source,
    *,
    rate_limiter: HostRateLimiter | None = None,
    now: datetime | None = None,
) -> RobotsCheckResult:
    checked_at = now or timezone.now()
    robots_url = _robots_url(source.base_url)
    parsed = urlparse(robots_url)
    allowed_hosts = frozenset({parsed.hostname or ""})

    request = SafeHttpRequest(
        url=robots_url,
        allowed_hosts=allowed_hosts,
        user_agent=ROBOTS_USER_AGENT,
        contact_email=ROBOTS_CONTACT_EMAIL,
        timeout_seconds=8,
        max_redirects=2,
        max_response_bytes=250_000,
        min_request_interval_seconds=1,
    )

    try:
        response = fetch_url_with_retries(
            request,
            rate_limiter=rate_limiter,
            max_attempts=1,
        )
    except HTTPError as exc:
        return _http_error_result(source, robots_url, checked_at, exc)
    except (SafeHttpError, URLError, TimeoutError, OSError) as exc:
        return RobotsCheckResult(
            source_id=source.id,
            source_key=source.source_key or str(source.id),
            robots_url=robots_url,
            status=Source.RobotsStatus.UNKNOWN,
            checked_at=checked_at,
            error=exc.__class__.__name__,
        )

    robots_txt = response.body.decode("utf-8", errors="replace")
    allowed = is_robots_allowed(robots_txt, ROBOTS_USER_AGENT, source.listing_url)
    return RobotsCheckResult(
        source_id=source.id,
        source_key=source.source_key or str(source.id),
        robots_url=robots_url,
        status=Source.RobotsStatus.ALLOWED if allowed else Source.RobotsStatus.RESTRICTED,
        checked_at=checked_at,
    )


def apply_robots_check_result(source: Source, result: RobotsCheckResult) -> Source:
    source.robots_status = result.status
    config = dict(source.config_json or {})
    config["robots_check"] = {
        "checked_at": result.checked_at.isoformat(),
        "robots_url": result.robots_url,
        "status": result.status,
        "error": result.error,
    }
    source.config_json = config
    source.config_version += 1
    source.save(update_fields=["robots_status", "config_json", "config_version", "updated_at"])
    return source


def _robots_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base_url.rstrip("/")
    return urljoin(f"{origin}/", "robots.txt")


def _http_error_result(
    source: Source,
    robots_url: str,
    checked_at: datetime,
    exc: HTTPError,
) -> RobotsCheckResult:
    if exc.code in {401, 403}:
        status = Source.RobotsStatus.RESTRICTED
    else:
        status = Source.RobotsStatus.UNKNOWN
    return RobotsCheckResult(
        source_id=source.id,
        source_key=source.source_key or str(source.id),
        robots_url=robots_url,
        status=status,
        checked_at=checked_at,
        error=f"http_{exc.code}",
    )
