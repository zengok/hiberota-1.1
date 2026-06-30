from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError, CommandParser

DEFAULT_BASE_URL = "https://staging.hiberota.com"
DEFAULT_PATHS = ("/", "/cagrilar/", "/health/live")


@dataclass(frozen=True, slots=True)
class LoadSample:
    path: str
    status_code: int
    elapsed_ms: float
    error: str = ""


@dataclass(frozen=True, slots=True)
class LoadSummary:
    total: int
    failures: int
    error_rate: float
    p95_ms: float
    max_ms: float


class Command(BaseCommand):
    help = "Run a small staging load smoke without adding external benchmarking dependencies."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL to test.")
        parser.add_argument("--requests", type=int, default=60, help="Total request count.")
        parser.add_argument("--concurrency", type=int, default=4, help="Concurrent worker count.")
        parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
        parser.add_argument("--path", action="append", default=[], help="Path to include. May be repeated.")
        parser.add_argument(
            "--max-p95-ms",
            type=float,
            default=1500.0,
            help="Fail when p95 latency exceeds this value.",
        )
        parser.add_argument(
            "--max-error-rate",
            type=float,
            default=0.0,
            help="Fail when error rate exceeds this value.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        base_url = _validated_base_url(str(options["base_url"]))
        total_requests = _positive_int(options["requests"], "requests")
        concurrency = _positive_int(options["concurrency"], "concurrency")
        timeout = float(options["timeout"])
        max_p95_ms = float(options["max_p95_ms"])
        max_error_rate = float(options["max_error_rate"])
        paths = tuple(str(path) for path in options["path"]) or DEFAULT_PATHS

        samples = run_load_smoke(
            base_url=base_url,
            paths=paths,
            total_requests=total_requests,
            concurrency=concurrency,
            timeout=timeout,
        )
        summary = summarize_samples(samples)

        self.stdout.write(f"Requests: {summary.total}")
        self.stdout.write(f"Failures: {summary.failures}")
        self.stdout.write(f"Error rate: {summary.error_rate:.2%}")
        self.stdout.write(f"p95: {summary.p95_ms:.1f} ms")
        self.stdout.write(f"max: {summary.max_ms:.1f} ms")

        slowest = sorted(samples, key=lambda sample: sample.elapsed_ms, reverse=True)[:5]
        for sample in slowest:
            detail = f" error={sample.error}" if sample.error else ""
            self.stdout.write(
                f"sample path={sample.path} status={sample.status_code} elapsed={sample.elapsed_ms:.1f}ms{detail}"
            )

        failures = []
        if summary.error_rate > max_error_rate:
            failures.append(f"error rate {summary.error_rate:.2%} exceeded {max_error_rate:.2%}")
        if summary.p95_ms > max_p95_ms:
            failures.append(f"p95 {summary.p95_ms:.1f} ms exceeded {max_p95_ms:.1f} ms")
        if failures:
            raise CommandError("Staging load smoke failed: " + "; ".join(failures))

        self.stdout.write(self.style.SUCCESS("Staging load smoke passed."))


def run_load_smoke(
    *,
    base_url: str,
    paths: tuple[str, ...],
    total_requests: int,
    concurrency: int,
    timeout: float,
) -> list[LoadSample]:
    planned_paths = [paths[index % len(paths)] for index in range(total_requests)]
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(_fetch_once, urljoin(f"{base_url}/", path.lstrip("/")), path, timeout)
            for path in planned_paths
        ]
        return [future.result() for future in as_completed(futures)]


def summarize_samples(samples: list[LoadSample]) -> LoadSummary:
    if not samples:
        return LoadSummary(total=0, failures=0, error_rate=0, p95_ms=0, max_ms=0)
    failures = sum(1 for sample in samples if sample.error or sample.status_code >= 500)
    latencies = sorted(sample.elapsed_ms for sample in samples)
    p95_index = max(0, int(len(latencies) * 0.95) - 1)
    return LoadSummary(
        total=len(samples),
        failures=failures,
        error_rate=failures / len(samples),
        p95_ms=latencies[p95_index],
        max_ms=latencies[-1],
    )


def _fetch_once(url: str, path: str, timeout: float) -> LoadSample:
    started = perf_counter()
    request = Request(url, headers={"User-Agent": "HibeRotaLoadSmoke/1.0"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            response.read(50_000)
            status_code = int(getattr(response, "status", 200))
            return LoadSample(path=path, status_code=status_code, elapsed_ms=_elapsed_ms(started))
    except HTTPError as exc:
        exc.read(10_000)
        return LoadSample(path=path, status_code=exc.code, elapsed_ms=_elapsed_ms(started), error=str(exc))
    except (TimeoutError, URLError) as exc:
        return LoadSample(path=path, status_code=0, elapsed_ms=_elapsed_ms(started), error=str(exc))


def _validated_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise CommandError("base-url must be an absolute https URL.")
    return value.rstrip("/")


def _positive_int(value: str | int, name: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise CommandError(f"{name} must be greater than zero.")
    return parsed


def _elapsed_ms(started: float) -> float:
    return (perf_counter() - started) * 1000
