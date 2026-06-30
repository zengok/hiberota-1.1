from __future__ import annotations

from django.contrib import admin

from .health import source_automation_metrics, source_health_label
from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = [
        "source_key",
        "name",
        "institution",
        "source_type",
        "status",
        "health_status",
        "crawl_interval_minutes",
        "health_score",
        "consecutive_failures",
        "last_crawl_status",
        "last_crawl_counts",
        "decision_mix",
        "last_http_statuses",
    ]
    list_filter = ["source_type", "status", "robots_status", "terms_status"]
    search_fields = ["source_key", "name", "adapter_key", "base_url", "listing_url", "institution__name"]
    autocomplete_fields = ["institution"]
    readonly_fields = ["last_success_at", "last_failure_at", "consecutive_failures", "health_score", "config_version"]

    @admin.display(description="Health")
    def health_status(self, obj: Source) -> str:
        return source_health_label(obj)

    @admin.display(description="Last crawl")
    def last_crawl_status(self, obj: Source) -> str:
        metrics = source_automation_metrics(obj)
        return metrics.last_run_status

    @admin.display(description="Crawl counts")
    def last_crawl_counts(self, obj: Source) -> str:
        metrics = source_automation_metrics(obj)
        return (
            f"disc:{metrics.discovered_count} fetch:{metrics.fetched_count} "
            f"new:{metrics.created_count} upd:{metrics.updated_count} "
            f"review:{metrics.review_count} fail:{metrics.failed_count}"
        )

    @admin.display(description="Publish/reject")
    def decision_mix(self, obj: Source) -> str:
        metrics = source_automation_metrics(obj)
        return (
            f"pub:{metrics.published_count} ({metrics.publish_rate_percent:.1f}%) "
            f"rej:{metrics.rejected_count} ({metrics.reject_rate_percent:.1f}%) "
            f"rev:{metrics.review_total_count} fp:{metrics.false_positive_count} "
            f"({metrics.false_positive_rate_percent:.1f}%)"
        )

    @admin.display(description="HTTP")
    def last_http_statuses(self, obj: Source) -> str:
        metrics = source_automation_metrics(obj)
        if not metrics.http_status_summary:
            return "-"
        return ", ".join(f"{key}:{value}" for key, value in sorted(metrics.http_status_summary.items()))
