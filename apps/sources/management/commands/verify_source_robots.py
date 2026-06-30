from __future__ import annotations

from typing import Any

from automation.http.client import HostRateLimiter
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.sources.compliance import apply_robots_check_result, check_source_robots
from apps.sources.models import Source

MAX_ROBOTS_CHECK_LIMIT = 250


class Command(BaseCommand):
    help = "Check robots.txt status for imported sources without crawling source content."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source-key", action="append", default=[], help="Limit check to one source key.")
        parser.add_argument("--limit", type=int, default=25, help="Maximum sources to check.")
        parser.add_argument("--commit", action="store_true", help="Persist robots_status changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        if limit < 1 or limit > MAX_ROBOTS_CHECK_LIMIT:
            raise CommandError(f"Limit must be between 1 and {MAX_ROBOTS_CHECK_LIMIT}.")

        source_keys = [str(key).strip() for key in options["source_key"] if str(key).strip()]
        queryset = Source.objects.select_related("institution").order_by("id")
        if source_keys:
            queryset = queryset.filter(source_key__in=source_keys)
        else:
            queryset = queryset.filter(robots_status=Source.RobotsStatus.UNKNOWN)

        rate_limiter = HostRateLimiter()
        checked = 0
        updated = 0
        counts: dict[str, int] = {}

        for source in queryset[:limit]:
            result = check_source_robots(source, rate_limiter=rate_limiter)
            checked += 1
            status = str(result.status)
            counts[status] = counts.get(status, 0) + 1
            self.stdout.write(
                f"{result.source_key} {status} robots={result.robots_url}"
                + (f" error={result.error}" if result.error else "")
            )
            if options["commit"]:
                apply_robots_check_result(source, result)
                updated += 1

        self.stdout.write(f"Checked sources: {checked}")
        self.stdout.write(f"Status counts: {counts}")
        if options["commit"]:
            self.stdout.write(self.style.SUCCESS(f"Updated sources: {updated}"))
        else:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to persist results."))
