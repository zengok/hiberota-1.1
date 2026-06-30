from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.calls.review_queue import ReviewQueueCategory, build_review_queue_report, parse_review_queue_category
from apps.ingestion.models import ReviewItem

REJECTABLE_CATEGORIES = (
    ReviewQueueCategory.CLOSED_SOURCE,
    ReviewQueueCategory.GUIDANCE_PAGE,
)

DEFAULT_REASONS = {
    ReviewQueueCategory.CLOSED_SOURCE: "Review queue triage rejected closed or restricted source.",
    ReviewQueueCategory.GUIDANCE_PAGE: "Review queue triage rejected guidance or general information page.",
}


class Command(BaseCommand):
    help = "Reject review-stage grant calls from a safe review queue category."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--category",
            required=True,
            choices=tuple(category.value for category in REJECTABLE_CATEGORIES),
            help="Safe review queue category to reject.",
        )
        parser.add_argument("--limit", type=int, default=50, help="Maximum matching calls to reject.")
        parser.add_argument("--reason", help="Operator-visible rejection reason. Defaults to the category reason.")
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        category = _rejectable_category(str(options["category"]))
        limit = int(options["limit"])
        if limit < 1:
            raise CommandError("limit must be greater than zero.")

        reason = str(options.get("reason") or DEFAULT_REASONS[category]).strip()
        if not reason:
            raise CommandError("reason cannot be blank.")

        report = build_review_queue_report()
        entries = report.entries_for(category)[:limit]
        call_ids = [entry.call.id for entry in entries]

        self.stdout.write(f"Matched {len(call_ids)} {category.value} review calls.")
        for entry in entries:
            call = entry.call
            self.stdout.write(f"{call.id}. {call.source.source_key} | {call.title} | {entry.reason}")

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to reject calls."))
            return

        rejected_at = timezone.now()
        with transaction.atomic():
            rejected_calls = GrantCall.objects.filter(
                id__in=call_ids,
                workflow_status=GrantCall.WorkflowStatus.REVIEW,
            ).update(
                workflow_status=GrantCall.WorkflowStatus.REJECTED,
                updated_at=rejected_at,
            )
            resolved_reviews = ReviewItem.objects.filter(
                grant_call_id__in=call_ids,
                status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            ).update(
                status=ReviewItem.Status.RESOLVED,
                resolution=reason,
                resolved_at=rejected_at,
                updated_at=rejected_at,
            )

        self.stdout.write(self.style.SUCCESS(f"Rejected calls: {rejected_calls}"))
        self.stdout.write(self.style.SUCCESS(f"Resolved review items: {resolved_reviews}"))


def _rejectable_category(value: str) -> ReviewQueueCategory:
    try:
        category = parse_review_queue_category(value)
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
    if category not in REJECTABLE_CATEGORIES:
        allowed = ", ".join(category.value for category in REJECTABLE_CATEGORIES)
        raise CommandError(f"Category '{category.value}' cannot be rejected by this command. Allowed: {allowed}.")
    return category
