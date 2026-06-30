from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError, CommandParser

DEFAULT_STAGING_URL = "https://staging.hiberota.com"
DEFAULT_TIMEOUT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class HttpSmokeResponse:
    url: str
    status_code: int
    content_type: str
    headers: dict[str, str]
    body: bytes


class Command(BaseCommand):
    help = "Verify that the public staging URL is served by the Django staging stack."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--base-url", default=DEFAULT_STAGING_URL, help="Staging base URL to verify.")
        parser.add_argument(
            "--timeout",
            type=float,
            default=DEFAULT_TIMEOUT_SECONDS,
            help="Request timeout in seconds.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        base_url = str(options["base_url"]).rstrip("/")
        timeout = float(options["timeout"])

        failures: list[str] = []
        health = _fetch(urljoin(f"{base_url}/", "health/live"), timeout)
        failures.extend(_verify_health_response(health))
        failures.extend(_verify_staging_noindex(health))

        home = _fetch(f"{base_url}/", timeout)
        failures.extend(_verify_home_response(home, base_url))
        failures.extend(_verify_staging_noindex(home))

        if failures:
            for failure in failures:
                self.stderr.write(f"- {failure}")
            raise CommandError("Staging smoke verification failed.")

        self.stdout.write(self.style.SUCCESS(f"Staging smoke verification passed for {base_url}."))


def _fetch(url: str, timeout: float) -> HttpSmokeResponse:
    request = Request(url, headers={"User-Agent": "HibeRotaStagingSmoke/1.0"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            headers = {key.lower(): value for key, value in response.headers.items()}
            body = response.read(250_000)
            return HttpSmokeResponse(
                url=url,
                status_code=getattr(response, "status", 200),
                content_type=headers.get("content-type", ""),
                headers=headers,
                body=body,
            )
    except HTTPError as exc:
        body = exc.read(10_000)
        headers = {key.lower(): value for key, value in exc.headers.items()}
        return HttpSmokeResponse(
            url=url,
            status_code=exc.code,
            content_type=headers.get("content-type", ""),
            headers=headers,
            body=body,
        )
    except URLError as exc:
        raise CommandError(f"Could not reach {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise CommandError(f"Timed out while reaching {url}.") from exc


def _verify_health_response(response: HttpSmokeResponse) -> list[str]:
    failures: list[str] = []
    if response.status_code != 200:
        failures.append(f"{response.url} returned HTTP {response.status_code}, expected 200.")
        return failures
    if not response.content_type.lower().startswith("application/json"):
        failures.append(f"{response.url} returned {response.content_type or 'no content-type'}, expected JSON.")
        return failures

    try:
        payload = json.loads(response.body.decode("utf-8"))
    except json.JSONDecodeError:
        failures.append(f"{response.url} did not return valid JSON.")
        return failures

    if payload.get("status") != "ok" or payload.get("service") != "hiberota":
        failures.append(f"{response.url} returned unexpected health payload: {payload!r}.")
    return failures


def _verify_staging_noindex(response: HttpSmokeResponse) -> list[str]:
    robots_header = response.headers.get("x-robots-tag", "").lower()
    if "noindex" not in robots_header or "nofollow" not in robots_header:
        return [f"{response.url} is missing X-Robots-Tag: noindex, nofollow."]
    return []


def _verify_home_response(response: HttpSmokeResponse, base_url: str) -> list[str]:
    failures: list[str] = []
    if response.status_code != 200:
        failures.append(f"{response.url} returned HTTP {response.status_code}, expected 200.")
        return failures
    html = response.body.decode("utf-8", errors="replace")
    expected_canonical = f'<link rel="canonical" href="{base_url}/"'
    if expected_canonical not in html:
        failures.append(f"{response.url} canonical does not point to {base_url}/.")
    if "https://hiberota.com/" in html:
        failures.append(f"{response.url} still contains production canonical/origin https://hiberota.com/.")
    return failures
