from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.db.models import Avg, Count, Q, QuerySet

from apps.calls.models import GrantCall
from apps.ingestion.models import ReviewItem
from apps.sources.models import Source


@dataclass(frozen=True, slots=True)
class SourceHealthSummary:
    total: int
    active: int
    paused: int
    degraded: int
    blocked: int
    manual_only: int
    average_health_score: float
    consecutive_failure_sources: int


@dataclass(frozen=True, slots=True)
class SourceAutomationMetrics:
    last_run_status: str
    last_run_started_at: datetime | None
    discovered_count: int
    fetched_count: int
    created_count: int
    updated_count: int
    review_count: int
    failed_count: int
    http_status_summary: dict[str, int]
    published_count: int
    rejected_count: int
    review_total_count: int
    false_positive_count: int
    publish_rate_percent: float
    reject_rate_percent: float
    false_positive_rate_percent: float


def source_health_summary(queryset: QuerySet[Source] | None = None) -> SourceHealthSummary:
    sources = queryset if queryset is not None else Source.objects.all()
    status_counts = {row["status"]: row["count"] for row in sources.values("status").annotate(count=Count("id"))}
    average = sources.aggregate(value=Avg("health_score"))["value"] or 0
    return SourceHealthSummary(
        total=sources.count(),
        active=status_counts.get(Source.Status.ACTIVE, 0),
        paused=status_counts.get(Source.Status.PAUSED, 0),
        degraded=status_counts.get(Source.Status.DEGRADED, 0),
        blocked=status_counts.get(Source.Status.BLOCKED, 0),
        manual_only=status_counts.get(Source.Status.MANUAL_ONLY, 0),
        average_health_score=float(average),
        consecutive_failure_sources=sources.filter(consecutive_failures__gt=0).count(),
    )


def source_health_label(source: Source) -> str:
    if source.status in {Source.Status.BLOCKED, Source.Status.MANUAL_ONLY}:
        return source.status
    if source.consecutive_failures >= 3:
        return "failing"
    if source.health_score < 60:
        return "degraded"
    return "healthy"


def source_automation_metrics(source: Source) -> SourceAutomationMetrics:
    last_run = source.crawl_runs.order_by("-started_at").first()
    decision_metrics = _source_decision_metrics(source)
    if last_run is None:
        return SourceAutomationMetrics(
            last_run_status="never",
            last_run_started_at=None,
            discovered_count=0,
            fetched_count=0,
            created_count=0,
            updated_count=0,
            review_count=0,
            failed_count=0,
            http_status_summary={},
            published_count=decision_metrics.published_count,
            rejected_count=decision_metrics.rejected_count,
            review_total_count=decision_metrics.review_total_count,
            false_positive_count=decision_metrics.false_positive_count,
            publish_rate_percent=decision_metrics.publish_rate_percent,
            reject_rate_percent=decision_metrics.reject_rate_percent,
            false_positive_rate_percent=decision_metrics.false_positive_rate_percent,
        )

    return SourceAutomationMetrics(
        last_run_status=last_run.status,
        last_run_started_at=last_run.started_at,
        discovered_count=last_run.discovered_count,
        fetched_count=last_run.fetched_count,
        created_count=last_run.created_count,
        updated_count=last_run.updated_count,
        review_count=last_run.review_count,
        failed_count=last_run.failed_count,
        http_status_summary={str(key): int(value) for key, value in last_run.http_status_summary.items()},
        published_count=decision_metrics.published_count,
        rejected_count=decision_metrics.rejected_count,
        review_total_count=decision_metrics.review_total_count,
        false_positive_count=decision_metrics.false_positive_count,
        publish_rate_percent=decision_metrics.publish_rate_percent,
        reject_rate_percent=decision_metrics.reject_rate_percent,
        false_positive_rate_percent=decision_metrics.false_positive_rate_percent,
    )


@dataclass(frozen=True, slots=True)
class _SourceDecisionMetrics:
    published_count: int
    rejected_count: int
    review_total_count: int
    false_positive_count: int
    publish_rate_percent: float
    reject_rate_percent: float
    false_positive_rate_percent: float


FALSE_POSITIVE_KEYWORDS = (
    "application process",
    "applying for funding",
    "applying-funding",
    "funding/applying",
    "funding stages",
    "guidance",
    "guide",
    "how to apply",
    "how-to-apply",
    "managing funds",
    "why applications",
)


def _source_decision_metrics(source: Source) -> _SourceDecisionMetrics:
    calls = GrantCall.objects.filter(source=source)
    published_count = calls.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED).count()
    rejected_count = calls.filter(workflow_status=GrantCall.WorkflowStatus.REJECTED).count()
    review_total_count = calls.filter(workflow_status=GrantCall.WorkflowStatus.REVIEW).count()
    false_positive_count = (
        calls.filter(
            _false_positive_filter(),
            workflow_status=GrantCall.WorkflowStatus.REJECTED,
        )
        .distinct()
        .count()
    )
    decided_count = published_count + rejected_count
    persisted_count = decided_count + review_total_count
    return _SourceDecisionMetrics(
        published_count=published_count,
        rejected_count=rejected_count,
        review_total_count=review_total_count,
        false_positive_count=false_positive_count,
        publish_rate_percent=_percentage(published_count, decided_count),
        reject_rate_percent=_percentage(rejected_count, decided_count),
        false_positive_rate_percent=_percentage(false_positive_count, persisted_count),
    )


def _false_positive_filter() -> Q:
    keyword_filter = Q()
    for keyword in FALSE_POSITIVE_KEYWORDS:
        keyword_filter |= Q(title__icontains=keyword)
        keyword_filter |= Q(official_url__icontains=keyword)
        keyword_filter |= Q(canonical_source_url__icontains=keyword)
    return keyword_filter | Q(review_items__reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED)


def _percentage(value: int, total: int) -> float:
    if total <= 0:
        return 0
    return round((value / total) * 100, 1)
