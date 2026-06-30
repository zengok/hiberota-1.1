from __future__ import annotations

from datetime import datetime

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone

from apps.calls.services import apply_availability_status
from apps.ingestion.models import ReviewItem

from .models import GrantCall

ADMIN_PUBLISH_REASON = "Admin review action approved for publication."
ADMIN_REJECT_REASON = "Admin review action rejected as not publishable."
MIN_ADMIN_PUBLISH_CONFIDENCE = 60


@admin.register(GrantCall)
class GrantCallAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "institution",
        "workflow_status",
        "availability_status",
        "deadline_at",
        "confidence_score",
        "published_at",
    ]
    list_filter = ["workflow_status", "availability_status", "is_featured", "institution", "source"]
    search_fields = ["title", "summary", "official_url", "canonical_source_url", "institution__name"]
    actions = ["publish_review_candidates", "reject_review_calls"]
    autocomplete_fields = [
        "source",
        "institution",
        "countries",
        "audiences",
        "sectors",
        "themes",
        "program_types",
        "organization_sizes",
        "regions",
    ]
    prepopulated_fields = {"slug": ("title",)}

    @admin.action(description="Uygun review çağrılarını yayınla")
    def publish_review_candidates(self, request: HttpRequest, queryset: QuerySet[GrantCall]) -> None:
        now = timezone.now()
        selected_count = queryset.count()
        candidates = list(_eligible_publish_queryset(queryset, now=now))
        candidate_ids = [call.id for call in candidates]

        with transaction.atomic():
            for call in candidates:
                call.workflow_status = GrantCall.WorkflowStatus.PUBLISHED
                call.published_at = now
                apply_availability_status(call, now=now)
                call.save(update_fields=["workflow_status", "published_at", "availability_status", "updated_at"])

            resolved_reviews = _resolve_open_review_items(
                call_ids=candidate_ids,
                reason=ADMIN_PUBLISH_REASON,
                resolved_at=now,
            )

        skipped_count = selected_count - len(candidates)
        if candidates:
            self.message_user(
                request,
                f"{len(candidates)} çağrı yayınlandı; {resolved_reviews} review kaydı çözüldü.",
                messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                (
                    f"{skipped_count} çağrı atlandı. Yalnızca review durumunda, güven skoru "
                    f"{MIN_ADMIN_PUBLISH_CONFIDENCE}+ olan, deadline'ı gelecek tarihli ve bloklayıcı "
                    "review nedeni olmayan çağrılar admin aksiyonuyla yayınlanır."
                ),
                messages.WARNING,
            )

    @admin.action(description="Seçili review çağrılarını reddet")
    def reject_review_calls(self, request: HttpRequest, queryset: QuerySet[GrantCall]) -> None:
        now = timezone.now()
        selected_count = queryset.count()
        review_call_ids = list(
            queryset.filter(workflow_status=GrantCall.WorkflowStatus.REVIEW).values_list("id", flat=True)
        )

        with transaction.atomic():
            rejected_calls = GrantCall.objects.filter(id__in=review_call_ids).update(
                workflow_status=GrantCall.WorkflowStatus.REJECTED,
                updated_at=now,
            )
            resolved_reviews = _resolve_open_review_items(
                call_ids=review_call_ids,
                reason=ADMIN_REJECT_REASON,
                resolved_at=now,
            )

        skipped_count = selected_count - rejected_calls
        if rejected_calls:
            self.message_user(
                request,
                f"{rejected_calls} review çağrısı reddedildi; {resolved_reviews} review kaydı çözüldü.",
                messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"{skipped_count} çağrı review durumunda olmadığı için atlandı.",
                messages.WARNING,
            )


def _eligible_publish_queryset(queryset: QuerySet[GrantCall], *, now: datetime) -> QuerySet[GrantCall]:
    return (
        queryset.filter(
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score__gte=MIN_ADMIN_PUBLISH_CONFIDENCE,
            official_url__gt="",
            canonical_source_url__gt="",
            availability_status__in=(
                GrantCall.AvailabilityStatus.OPEN,
                GrantCall.AvailabilityStatus.CLOSING_SOON,
                GrantCall.AvailabilityStatus.UPCOMING,
            ),
            deadline_at__gt=now,
        )
        .exclude(
            review_items__status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            review_items__reason_code__in=(
                ReviewItem.ReasonCode.DEADLINE_CONFLICT,
                ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                ReviewItem.ReasonCode.SOURCE_RESTRICTED,
                ReviewItem.ReasonCode.DUPLICATE_CANDIDATE,
                ReviewItem.ReasonCode.PARSER_ERROR,
            ),
        )
        .distinct()
    )


def _resolve_open_review_items(*, call_ids: list[int], reason: str, resolved_at: datetime) -> int:
    if not call_ids:
        return 0
    return ReviewItem.objects.filter(
        grant_call_id__in=call_ids,
        status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
    ).update(
        status=ReviewItem.Status.RESOLVED,
        resolution=reason,
        resolved_at=resolved_at,
        updated_at=resolved_at,
    )
