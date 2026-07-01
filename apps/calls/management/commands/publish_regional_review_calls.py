from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.calls.review_queue import ReviewQueueCategory, build_review_queue_report
from apps.calls.services import apply_availability_status
from apps.ingestion.models import ReviewItem

REGIONAL_PUBLISH_REASON = "Published after regional priority review for Türkiye and Europe."
BLOCKING_REASONS = {
    ReviewItem.ReasonCode.DEADLINE_CONFLICT,
    ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
    ReviewItem.ReasonCode.SOURCE_RESTRICTED,
    ReviewItem.ReasonCode.DUPLICATE_CANDIDATE,
    ReviewItem.ReasonCode.PARSER_ERROR,
}


class Command(BaseCommand):
    help = "Publish safe Türkiye and Europe review calls so they become visible on public pages."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--region", choices=("tr", "europe", "tr-europe"), default="tr-europe")
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--min-confidence", type=int, default=60)
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        min_confidence = int(options["min_confidence"])
        if limit < 1:
            raise CommandError("limit must be greater than zero.")
        if min_confidence < 0 or min_confidence > 100:
            raise CommandError("min-confidence must be between 0 and 100.")

        candidates = list(_candidate_queryset(region=str(options["region"]), min_confidence=min_confidence)[:limit])
        safe_call_ids, skipped_ids = _safe_candidate_ids(candidates)

        self.stdout.write(f"Matched regional review calls: {len(candidates)}")
        self.stdout.write(f"Safe publish candidates: {len(safe_call_ids)}")
        self.stdout.write(f"Skipped unsafe candidates: {len(skipped_ids)}")
        for call in candidates[:30]:
            marker = "publish" if call.id in safe_call_ids else "skip"
            deadline = call.deadline_at.date().isoformat() if call.deadline_at else "missing"
            self.stdout.write(
                f"{marker}: {call.id}. {call.source.source_key} | {call.source.institution.country.code} | "
                f"confidence={call.confidence_score} | deadline={deadline} | {call.title[:90]}"
            )

        if not options["commit"]:
            self.stdout.write(self.style.SUCCESS("Dry run complete. Run again with --commit to publish calls."))
            return

        published_at = timezone.now()
        with transaction.atomic():
            calls = GrantCall.objects.filter(id__in=safe_call_ids).select_for_update()
            published_count = 0
            for call in calls:
                call.workflow_status = GrantCall.WorkflowStatus.PUBLISHED
                call.published_at = published_at
                apply_availability_status(call, now=published_at)
                call.save(update_fields=["workflow_status", "published_at", "availability_status", "updated_at"])
                published_count += 1

            resolved_reviews = ReviewItem.objects.filter(
                grant_call_id__in=safe_call_ids,
                status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            ).update(
                status=ReviewItem.Status.RESOLVED,
                resolution=REGIONAL_PUBLISH_REASON,
                resolved_at=published_at,
                updated_at=published_at,
            )

        self.stdout.write(self.style.SUCCESS(f"Published calls: {published_count}"))
        self.stdout.write(self.style.SUCCESS(f"Resolved review items: {resolved_reviews}"))


def _candidate_queryset(*, region: str, min_confidence: int):
    region_filter = Q()
    if region in {"tr", "tr-europe"}:
        region_filter |= Q(source__institution__country__code="TR")
    if region in {"europe", "tr-europe"}:
        region_filter |= Q(source__institution__country__is_europe=True) | Q(source__institution__country__code="EU")

    blocking_reviews = ReviewItem.objects.filter(
        grant_call_id=OuterRef("pk"),
        status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
        reason_code__in=BLOCKING_REASONS,
    )
    return (
        GrantCall.objects.filter(
            region_filter,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score__gte=min_confidence,
        )
        .annotate(has_blocking_review=Exists(blocking_reviews))
        .filter(has_blocking_review=False)
        .select_related("source", "source__institution", "source__institution__country")
        .order_by("source__institution__country__code", "id")
        .distinct()
    )


def _safe_candidate_ids(candidates: list[GrantCall]) -> tuple[set[int], set[int]]:
    report = build_review_queue_report(queryset=GrantCall.objects.filter(id__in=[call.id for call in candidates]))
    unsafe_categories = {ReviewQueueCategory.CLOSED_SOURCE, ReviewQueueCategory.GUIDANCE_PAGE}
    unsafe_ids = {entry.call.id for entry in report.entries if entry.category in unsafe_categories}
    candidate_ids = {call.id for call in candidates}
    return candidate_ids - unsafe_ids, unsafe_ids
