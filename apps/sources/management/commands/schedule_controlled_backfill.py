from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import QuerySet

from apps.sources.locks import CrawlLock
from apps.sources.models import Source
from apps.sources.tasks import crawl_source

MAX_BACKFILL_LIMIT = 100


@dataclass(frozen=True, slots=True)
class BackfillPlan:
    sources: tuple[Source, ...]
    skipped_locked: int = 0


class Command(BaseCommand):
    help = "Schedule a controlled source crawl backfill through Celery."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source-key", action="append", default=[], help="Limit backfill to one source key.")
        parser.add_argument("--limit", type=int, default=10, help="Maximum number of sources to enqueue.")
        parser.add_argument("--queue", default="celery", help="Celery queue name.")
        parser.add_argument("--countdown-step", type=int, default=30, help="Seconds between queued source tasks.")
        parser.add_argument("--include-paused", action="store_true", help="Include paused sources for manual backfill.")
        parser.add_argument("--commit", action="store_true", help="Enqueue tasks. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        countdown_step = int(options["countdown_step"])
        if limit < 1 or limit > MAX_BACKFILL_LIMIT:
            raise CommandError(f"Limit must be between 1 and {MAX_BACKFILL_LIMIT}.")
        if countdown_step < 0:
            raise CommandError("countdown-step must be zero or greater.")

        source_keys = tuple(str(key).strip() for key in options["source_key"] if str(key).strip())
        plan = _build_backfill_plan(
            source_keys=source_keys,
            limit=limit,
            include_paused=bool(options["include_paused"]),
        )

        self.stdout.write(f"Planned sources: {len(plan.sources)}")
        if plan.skipped_locked:
            self.stdout.write(f"Skipped locked sources: {plan.skipped_locked}")

        for index, source in enumerate(plan.sources, start=1):
            self.stdout.write(
                f"{index}. {source.source_key or source.id} | {source.status} | "
                f"{source.adapter_key} | countdown={(index - 1) * countdown_step}s"
            )

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to enqueue tasks."))
            return

        for index, source in enumerate(plan.sources):
            crawl_source.apply_async(
                args=[source.id],
                countdown=index * countdown_step,
                queue=str(options["queue"]),
            )

        self.stdout.write(self.style.SUCCESS(f"Queued {len(plan.sources)} source backfill task(s)."))


def _build_backfill_plan(*, source_keys: tuple[str, ...], limit: int, include_paused: bool) -> BackfillPlan:
    queryset = _source_queryset(source_keys=source_keys, include_paused=include_paused)
    selected_sources: list[Source] = []
    skipped_locked = 0

    for source in queryset[: limit + MAX_BACKFILL_LIMIT]:
        if len(selected_sources) >= limit:
            break
        if CrawlLock(source_id=source.id).acquire():
            CrawlLock(source_id=source.id).release()
            selected_sources.append(source)
        else:
            skipped_locked += 1

    return BackfillPlan(sources=tuple(selected_sources), skipped_locked=skipped_locked)


def _source_queryset(*, source_keys: tuple[str, ...], include_paused: bool) -> QuerySet[Source]:
    statuses = [Source.Status.ACTIVE]
    if include_paused:
        statuses.append(Source.Status.PAUSED)

    queryset = Source.objects.filter(status__in=statuses).select_related("institution").order_by("id")
    if source_keys:
        queryset = queryset.filter(source_key__in=source_keys)
    return queryset
