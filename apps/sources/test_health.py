from __future__ import annotations

from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.ingestion.models import CrawlRun, ReviewItem
from apps.institutions.models import Country, Institution
from apps.sources.admin import SourceAdmin
from apps.sources.health import source_automation_metrics, source_health_label, source_health_summary
from apps.sources.models import Source


class SourceHealthTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.institution = Institution.objects.create(name="Kurum", slug="kurum", country=self.country)

    def create_source(self, **overrides: object) -> Source:
        values = {
            "institution": self.institution,
            "name": f"Kaynak {Source.objects.count() + 1}",
            "base_url": "https://example.org",
            "listing_url": f"https://example.org/calls/{Source.objects.count() + 1}",
            "source_type": Source.SourceType.HTML,
            "adapter_key": f"kurum_html_v{Source.objects.count() + 1}",
        } | overrides
        return Source.objects.create(**values)

    def test_source_health_summary_counts_statuses(self) -> None:
        self.create_source()
        self.create_source(status=Source.Status.DEGRADED, health_score=50, consecutive_failures=2)
        self.create_source(status=Source.Status.BLOCKED, health_score=0, consecutive_failures=5)

        summary = source_health_summary()

        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.active, 1)
        self.assertEqual(summary.degraded, 1)
        self.assertEqual(summary.blocked, 1)
        self.assertEqual(summary.consecutive_failure_sources, 2)

    def test_source_health_label_uses_failures_and_status(self) -> None:
        healthy = self.create_source()
        failing = self.create_source(consecutive_failures=3)
        blocked = self.create_source(status=Source.Status.BLOCKED)

        self.assertEqual(source_health_label(healthy), "healthy")
        self.assertEqual(source_health_label(failing), "failing")
        self.assertEqual(source_health_label(blocked), Source.Status.BLOCKED)

    def test_source_automation_metrics_reports_last_crawl_run(self) -> None:
        source = self.create_source()
        CrawlRun.objects.create(
            source=source,
            trigger_type=CrawlRun.TriggerType.BACKFILL,
            status=CrawlRun.Status.COMPLETED,
            started_at=timezone.now(),
            discovered_count=4,
            fetched_count=3,
            created_count=2,
            updated_count=1,
            review_count=1,
            failed_count=1,
            http_status_summary={"200": 3, "404": 1},
        )

        metrics = source_automation_metrics(source)

        self.assertEqual(metrics.last_run_status, CrawlRun.Status.COMPLETED)
        self.assertEqual(metrics.discovered_count, 4)
        self.assertEqual(metrics.fetched_count, 3)
        self.assertEqual(metrics.created_count, 2)
        self.assertEqual(metrics.updated_count, 1)
        self.assertEqual(metrics.review_count, 1)
        self.assertEqual(metrics.failed_count, 1)
        self.assertEqual(metrics.http_status_summary, {"200": 3, "404": 1})

    def test_source_automation_metrics_reports_publish_reject_and_false_positive_rates(self) -> None:
        source = self.create_source()
        CrawlRun.objects.create(
            source=source,
            trigger_type=CrawlRun.TriggerType.BACKFILL,
            status=CrawlRun.Status.COMPLETED,
            started_at=timezone.now(),
        )
        self.create_call(
            source=source,
            title="Published grant",
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
        )
        guidance = self.create_call(
            source=source,
            title="Application Process",
            workflow_status=GrantCall.WorkflowStatus.REJECTED,
        )
        ReviewItem.objects.create(grant_call=guidance, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)
        restricted = self.create_call(
            source=source,
            title="Closed official call",
            workflow_status=GrantCall.WorkflowStatus.REJECTED,
        )
        ReviewItem.objects.create(grant_call=restricted, reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED)
        self.create_call(
            source=source,
            title="Manual review call",
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )

        metrics = source_automation_metrics(source)

        self.assertEqual(metrics.published_count, 1)
        self.assertEqual(metrics.rejected_count, 2)
        self.assertEqual(metrics.review_total_count, 1)
        self.assertEqual(metrics.false_positive_count, 2)
        self.assertEqual(metrics.publish_rate_percent, 33.3)
        self.assertEqual(metrics.reject_rate_percent, 66.7)
        self.assertEqual(metrics.false_positive_rate_percent, 50.0)

    def test_source_automation_metrics_handles_sources_without_runs(self) -> None:
        source = self.create_source()

        metrics = source_automation_metrics(source)

        self.assertEqual(metrics.last_run_status, "never")
        self.assertEqual(metrics.discovered_count, 0)
        self.assertEqual(metrics.http_status_summary, {})

    def test_source_admin_exposes_crawl_metrics(self) -> None:
        source = self.create_source()
        CrawlRun.objects.create(
            source=source,
            trigger_type=CrawlRun.TriggerType.BACKFILL,
            status=CrawlRun.Status.FAILED,
            started_at=timezone.now(),
            discovered_count=1,
            fetched_count=0,
            failed_count=1,
            http_status_summary={"500": 1},
        )
        admin = SourceAdmin(Source, AdminSite())

        self.assertEqual(admin.last_crawl_status(source), CrawlRun.Status.FAILED)
        self.assertEqual(admin.last_crawl_counts(source), "disc:1 fetch:0 new:0 upd:0 review:0 fail:1")
        self.assertEqual(admin.last_http_statuses(source), "500:1")

    def test_source_admin_exposes_decision_mix(self) -> None:
        source = self.create_source()
        CrawlRun.objects.create(
            source=source,
            trigger_type=CrawlRun.TriggerType.BACKFILL,
            status=CrawlRun.Status.COMPLETED,
            started_at=timezone.now(),
        )
        self.create_call(
            source=source,
            title="Published grant",
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
        )
        self.create_call(
            source=source,
            title="Funding Stages",
            workflow_status=GrantCall.WorkflowStatus.REJECTED,
        )
        admin = SourceAdmin(Source, AdminSite())

        self.assertEqual(admin.decision_mix(source), "pub:1 (50.0%) rej:1 (50.0%) rev:0 fp:1 (50.0%)")

    def create_call(self, *, source: Source, title: str, workflow_status: str) -> GrantCall:
        count = GrantCall.objects.count() + 1
        now = timezone.now()
        return GrantCall.objects.create(
            title=title,
            slug=f"source-health-call-{count}",
            source=source,
            institution=self.institution,
            official_url=f"https://example.org/calls/{count}",
            canonical_source_url=f"https://example.org/calls/{count}",
            fingerprint=f"source-health-fingerprint-{count}",
            first_seen_at=now,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            workflow_status=workflow_status,
        )
