from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.ingestion.models import ReviewItem

FALSE_DEADLINE_CONFLICT_RESOLUTION = "Resolved by review reason normalization: missing dates are low confidence."


class Command(BaseCommand):
    help = "Resolve stale review reason codes that no longer match parser validation semantics."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--limit", type=int, default=500, help="Maximum false deadline conflicts to normalize.")
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        if limit < 1:
            self.stderr.write("limit must be greater than zero.")
            return

        false_conflicts = list(_false_deadline_conflicts()[:limit])
        call_ids_missing_dates = [
            review.grant_call_id
            for review in false_conflicts
            if review.grant_call_id
            and review.grant_call.application_open_at is None
            and review.grant_call.deadline_at is None
        ]

        self.stdout.write(f"False deadline conflicts matched: {len(false_conflicts)}")
        self.stdout.write(f"Missing-date calls needing low_confidence review: {len(set(call_ids_missing_dates))}")
        for review in false_conflicts[:20]:
            call = review.grant_call
            self.stdout.write(
                f"{review.id}. call={call.id} source={call.source.source_key} "
                f"open={call.application_open_at or 'missing'} deadline={call.deadline_at or 'missing'} "
                f"title={call.title[:90]}"
            )

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to normalize reviews."))
            return

        resolved_at = timezone.now()
        with transaction.atomic():
            created_or_reopened = _ensure_low_confidence_reviews(call_ids_missing_dates)
            updated = ReviewItem.objects.filter(id__in=[review.id for review in false_conflicts]).update(
                status=ReviewItem.Status.RESOLVED,
                resolution=FALSE_DEADLINE_CONFLICT_RESOLUTION,
                resolved_at=resolved_at,
                updated_at=resolved_at,
            )

        self.stdout.write(self.style.SUCCESS(f"Resolved false deadline conflicts: {updated}"))
        self.stdout.write(self.style.SUCCESS(f"Created or reopened low_confidence reviews: {created_or_reopened}"))


def _false_deadline_conflicts():
    return (
        ReviewItem.objects.filter(
            reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
            status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            grant_call__isnull=False,
        )
        .filter(
            Q(grant_call__application_open_at__isnull=True)
            | Q(grant_call__deadline_at__isnull=True)
            | Q(grant_call__deadline_at__gte=F("grant_call__application_open_at"))
        )
        .exclude(
            grant_call__application_open_at__isnull=False,
            grant_call__deadline_at__isnull=False,
            grant_call__deadline_at__lt=F("grant_call__application_open_at"),
        )
        .select_related("grant_call", "grant_call__source")
        .order_by("id")
    )


def _ensure_low_confidence_reviews(call_ids: list[int]) -> int:
    changed = 0
    for call_id in sorted(set(call_ids)):
        review, created = ReviewItem.objects.get_or_create(
            grant_call_id=call_id,
            reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE,
            defaults={"severity": ReviewItem.Severity.MEDIUM},
        )
        if created:
            changed += 1
            continue
        if review.status == ReviewItem.Status.RESOLVED:
            review.status = ReviewItem.Status.OPEN
            review.resolution = ""
            review.resolved_at = None
            review.save(update_fields=["status", "resolution", "resolved_at", "updated_at"])
            changed += 1
    return changed
