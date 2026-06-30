from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.calls.services import apply_availability_status
from apps.ingestion.models import ReviewItem


class Command(BaseCommand):
    help = "Publish selected review-stage grant calls and resolve their open review items."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--call-id", action="append", default=[], help="GrantCall id to publish. May be repeated.")
        parser.add_argument("--reason", required=True, help="Operator-visible publish reason.")
        parser.add_argument("--min-confidence", type=int, default=60, help="Minimum confidence score required.")
        parser.add_argument(
            "--allow-missing-deadline",
            action="store_true",
            help="Allow publishing a reviewed call whose deadline is not known.",
        )
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        call_ids = _parse_call_ids(options["call_id"])
        reason = str(options["reason"]).strip()
        min_confidence = int(options["min_confidence"])
        allow_missing_deadline = bool(options["allow_missing_deadline"])
        if not reason:
            raise CommandError("reason cannot be blank.")
        if min_confidence < 0 or min_confidence > 100:
            raise CommandError("min-confidence must be between 0 and 100.")

        calls = list(GrantCall.objects.filter(id__in=call_ids).select_related("source").order_by("id"))
        _validate_calls(
            calls=calls,
            requested_ids=call_ids,
            min_confidence=min_confidence,
            allow_missing_deadline=allow_missing_deadline,
        )

        self.stdout.write(f"Matched calls: {len(calls)}")
        for call in calls:
            deadline = call.deadline_at.date().isoformat() if call.deadline_at else "missing"
            self.stdout.write(
                f"{call.id}. {call.source.source_key} | confidence={call.confidence_score} | "
                f"deadline={deadline} | {call.title} | {call.canonical_source_url}"
            )

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to publish calls."))
            return

        published_at = timezone.now()
        with transaction.atomic():
            for call in calls:
                call.workflow_status = GrantCall.WorkflowStatus.PUBLISHED
                call.published_at = published_at
                apply_availability_status(call, now=published_at)
                call.save(update_fields=["workflow_status", "published_at", "availability_status", "updated_at"])

            updated_reviews = ReviewItem.objects.filter(
                grant_call_id__in=call_ids,
                status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            ).update(
                status=ReviewItem.Status.RESOLVED,
                resolution=reason,
                resolved_at=published_at,
                updated_at=published_at,
            )

        self.stdout.write(self.style.SUCCESS(f"Published calls: {len(calls)}"))
        self.stdout.write(self.style.SUCCESS(f"Resolved review items: {updated_reviews}"))


def _validate_calls(
    *,
    calls: list[GrantCall],
    requested_ids: tuple[int, ...],
    min_confidence: int,
    allow_missing_deadline: bool,
) -> None:
    found_ids = {call.id for call in calls}
    missing_ids = sorted(set(requested_ids) - found_ids)
    if missing_ids:
        raise CommandError(f"Call ids not found: {', '.join(str(call_id) for call_id in missing_ids)}")

    non_review = [call.id for call in calls if call.workflow_status != GrantCall.WorkflowStatus.REVIEW]
    if non_review:
        raise CommandError(f"Only review calls can be published by this command: {', '.join(map(str, non_review))}")

    low_confidence = [call.id for call in calls if call.confidence_score < min_confidence]
    if low_confidence:
        raise CommandError(
            "Call confidence below threshold: "
            + ", ".join(f"{call.id} ({call.confidence_score})" for call in calls if call.id in low_confidence)
        )

    missing_deadline = [call.id for call in calls if call.deadline_at is None]
    if missing_deadline and not allow_missing_deadline:
        raise CommandError(
            "Call deadline is missing. Re-run with --allow-missing-deadline after manual review: "
            + ", ".join(str(call_id) for call_id in missing_deadline)
        )


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
