from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.calls.review_queue import (
    ReviewQueueCategory,
    build_review_queue_report,
    category_values,
    parse_review_queue_category,
)


class Command(BaseCommand):
    help = "Report review-stage grant calls by closed source, guidance page, publish candidate, and manual review."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--category", choices=tuple(category_values()), help="Only print one report category.")
        parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print per category.")
        parser.add_argument(
            "--min-publish-confidence",
            type=int,
            default=60,
            help="Minimum confidence required to classify a review call as a publish candidate.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        min_publish_confidence = int(options["min_publish_confidence"])
        if limit < 1:
            raise CommandError("limit must be greater than zero.")
        if min_publish_confidence < 0 or min_publish_confidence > 100:
            raise CommandError("min-publish-confidence must be between 0 and 100.")

        category = _category_from_option(options.get("category"))
        report = build_review_queue_report(min_publish_confidence=min_publish_confidence)
        counts = report.counts_by_category()

        self.stdout.write("Review queue summary")
        for report_category in ReviewQueueCategory:
            self.stdout.write(f"- {report_category.value}: {counts[report_category]}")

        categories = (category,) if category else tuple(ReviewQueueCategory)
        for report_category in categories:
            entries = tuple(entry for entry in report.entries_for(report_category)[:limit])
            self.stdout.write("")
            self.stdout.write(f"{report_category.value} ({counts[report_category]})")
            if not entries:
                self.stdout.write("  No matching review calls.")
                continue
            for entry in entries:
                call = entry.call
                deadline = call.deadline_at.date().isoformat() if call.deadline_at else "missing"
                reasons = ",".join(entry.open_reason_codes) if entry.open_reason_codes else "none"
                self.stdout.write(
                    "  "
                    f"{call.id}. {call.source.source_key} | confidence={call.confidence_score} | "
                    f"status={call.availability_status} | deadline={deadline} | "
                    f"reasons={reasons} | {call.title} | {entry.reason}"
                )


def _category_from_option(value: str | None) -> ReviewQueueCategory | None:
    if not value:
        return None
    try:
        return parse_review_queue_category(value)
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
