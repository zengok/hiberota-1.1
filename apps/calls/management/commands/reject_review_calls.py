from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.ingestion.models import ReviewItem


class Command(BaseCommand):
    help = "Reject selected review-stage grant calls and resolve their open review items."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--call-id", action="append", default=[], help="GrantCall id to reject. May be repeated.")
        parser.add_argument("--reason", required=True, help="Operator-visible rejection reason.")
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        call_ids = _parse_call_ids(options["call_id"])
        reason = str(options["reason"]).strip()
        if not reason:
            raise CommandError("reason cannot be blank.")

        calls = list(GrantCall.objects.filter(id__in=call_ids).select_related("source").order_by("id"))
        found_ids = {call.id for call in calls}
        missing_ids = sorted(set(call_ids) - found_ids)
        if missing_ids:
            raise CommandError(f"Call ids not found: {', '.join(str(call_id) for call_id in missing_ids)}")

        non_review = [call.id for call in calls if call.workflow_status != GrantCall.WorkflowStatus.REVIEW]
        if non_review:
            raise CommandError(f"Only review calls can be rejected by this command: {', '.join(map(str, non_review))}")

        self.stdout.write(f"Matched calls: {len(calls)}")
        for call in calls:
            self.stdout.write(f"{call.id}. {call.source.source_key} | {call.title} | {call.canonical_source_url}")

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to reject calls."))
            return

        resolved_at = timezone.now()
        with transaction.atomic():
            updated_calls = GrantCall.objects.filter(
                id__in=call_ids, workflow_status=GrantCall.WorkflowStatus.REVIEW
            ).update(
                workflow_status=GrantCall.WorkflowStatus.REJECTED,
                updated_at=resolved_at,
            )
            updated_reviews = ReviewItem.objects.filter(
                grant_call_id__in=call_ids,
                status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            ).update(
                status=ReviewItem.Status.RESOLVED,
                resolution=reason,
                resolved_at=resolved_at,
                updated_at=resolved_at,
            )

        self.stdout.write(self.style.SUCCESS(f"Rejected calls: {updated_calls}"))
        self.stdout.write(self.style.SUCCESS(f"Resolved review items: {updated_reviews}"))


def _parse_call_ids(values: list[str]) -> tuple[int, ...]:
    parsed: list[int] = []
    for value in values:
        try:
            call_id = int(value)
        except ValueError as exc:
            raise CommandError(f"Invalid call id: {value}") from exc
        if call_id < 1:
            raise CommandError(f"Invalid call id: {value}")
        parsed.append(call_id)
    if not parsed:
        raise CommandError("At least one --call-id is required.")
    return tuple(dict.fromkeys(parsed))
