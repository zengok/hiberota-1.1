from __future__ import annotations

import io
import ipaddress
import socket
import time
import urllib.robotparser
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import Request, urlopen


class SafeHttpError(RuntimeError):
    pass


class UnsafeUrlError(SafeHttpError):
    pass


@dataclass(frozen=True, slots=True)
class SafeHttpRequest:
    url: str
    allowed_hosts: frozenset[str]
    user_agent: str
    contact_email: str
    timeout_seconds: float = 10
    max_redirects: int = 3
    max_response_bytes: int = 2_000_000
    min_request_interval_seconds: float = 1
    robots_txt: str | None = None
    allowed_content_types: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "application/atom+xml",
                "application/json",
                "application/rss+xml",
                "application/xml",
                "text/csv",
                "text/html",
                "text/plain",
                "text/xml",
            }
        )
    )


@dataclass(frozen=True, slots=True)
class SafeHttpResponse:
    final_url: str
    status_code: int
    content_type: str
    body: bytes
    headers: Mapping[str, str]


class HostRateLimiter:
    def __init__(self) -> None:
        self._last_request_at: dict[str, float] = {}

    def wait(self, host: str, min_interval_seconds: float) -> None:
        now = time.monotonic()
        next_allowed_at = self._last_request_at.get(host, 0) + min_interval_seconds
        sleep_seconds = max(0.0, next_allowed_at - now)
        if sleep_seconds:
            time.sleep(sleep_seconds)
        self._last_request_at[host] = time.monotonic()


AddressResolver = Callable[[str, int], list[str]]


def default_resolver(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return sorted({str(info[4][0]) for info in infos})


def fetch_url(
    request: SafeHttpRequest,
    *,
    resolver: AddressResolver = default_resolver,
    rate_limiter: HostRateLimiter | None = None,
) -> SafeHttpResponse:
    current_url = request.url
    redirects = 0
    limiter = rate_limiter or HostRateLimiter()

    while True:
        parsed = validate_target_url(current_url, request.allowed_hosts, resolver=resolver)
        if request.robots_txt is not None and not is_robots_allowed(
            request.robots_txt,
            request.user_agent,
            current_url,
        ):
            raise SafeHttpError("robots.txt disallows this URL.")
        limiter.wait(parsed.hostname or "", request.min_request_interval_seconds)
        raw_response = _open_url(current_url, request)
        status_code = getattr(raw_response, "status", 200)
        headers = {key.lower(): value for key, value in raw_response.headers.items()}

        if status_code in {301, 302, 303, 307, 308}:
            redirects += 1
            if redirects > request.max_redirects:
                raise SafeHttpError("Maximum redirect count exceeded.")
            location = headers.get("location")
            if not location:
                raise SafeHttpError("Redirect response has no location header.")
            current_url = urljoin(current_url, location)
            continue

        content_type = headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()
        if content_type and content_type not in request.allowed_content_types:
            raise SafeHttpError(f"Unsupported content type: {content_type}")

        body = _read_limited(raw_response, request.max_response_bytes)
        return SafeHttpResponse(
            final_url=current_url,
            status_code=status_code,
            content_type=content_type,
            body=body,
            headers=headers,
        )


def fetch_url_with_retries(
    request: SafeHttpRequest,
    *,
    resolver: AddressResolver = default_resolver,
    rate_limiter: HostRateLimiter | None = None,
    max_attempts: int = 2,
    base_backoff_seconds: float = 1,
) -> SafeHttpResponse:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fetch_url(request, resolver=resolver, rate_limiter=rate_limiter)
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == max_attempts:
                raise
            _sleep_for_retry(dict(exc.headers.items()), attempt, base_backoff_seconds)
        except URLError as exc:
            last_error = exc
            if attempt == max_attempts:
                raise
            time.sleep(base_backoff_seconds * attempt)

    raise SafeHttpError("HTTP request failed after retries.") from last_error


def validate_target_url(
    url: str,
    allowed_hosts: frozenset[str],
    *,
    resolver: AddressResolver = default_resolver,
) -> ParseResult:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs are allowed.")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Userinfo in URL is not allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a hostname.")
    if parsed.hostname not in allowed_hosts:
        raise UnsafeUrlError("URL host is not allowlisted.")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in {80, 443}:
        raise UnsafeUrlError("Only ports 80 and 443 are allowed.")

    for address in resolver(parsed.hostname, port):
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise UnsafeUrlError("URL resolves to a non-public IP address.")

    return parsed


def is_robots_allowed(robots_txt: str, user_agent: str, url: str) -> bool:
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(io.StringIO(robots_txt).read().splitlines())
    return parser.can_fetch(user_agent, url)


def _open_url(url: str, request: SafeHttpRequest) -> Any:
    headers = {
        "User-Agent": request.user_agent,
        "From": request.contact_email,
        "Accept": ", ".join(sorted(request.allowed_content_types)),
    }
    urllib_request = Request(url, headers=headers, method="GET")
    # URL is allowlisted and IP-validated before this call.
    return urlopen(urllib_request, timeout=request.timeout_seconds)  # nosec B310


def _read_limited(response: Any, max_response_bytes: int) -> bytes:
    body = response.read(max_response_bytes + 1)
    if len(body) > max_response_bytes:
        raise SafeHttpError("Response exceeded maximum byte limit.")
    return body


def _sleep_for_retry(headers: Mapping[str, str], attempt: int, base_backoff_seconds: float) -> None:
    retry_after = headers.get("Retry-After")
    if retry_after:
        try:
            delay = float(retry_after)
        except ValueError:
            retry_at = parsedate_to_datetime(retry_after)
            delay = max(0.0, retry_at.timestamp() - time.time())
        time.sleep(delay)
        return

    time.sleep(base_backoff_seconds * attempt)
