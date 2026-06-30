from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from apps.calls.audit import build_call_data_quality_report
from apps.calls.models import GrantCall
from apps.ingestion.models import ReviewItem
from apps.institutions.models import Country, Institution
from apps.sources.models import Source


class CallDataQualityReportTests(TestCase):
    def setUp(self) -> None:
        self.now = timezone.now()
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")
        self.other_institution = Institution.objects.create(
            country=self.country,
            name="Baska Kurum",
            slug="baska-kurum",
        )
        self.source = self._create_source("source-a")
        self.other_source = self._create_source("source-b")

    def test_report_flags_semantic_duplicate_candidates(self) -> None:
        deadline = self.now + timedelta(days=20)
        first = self._create_call(
            title="KOBI Hibe Programi",
            source=self.source,
            official_url="https://example.org/calls/1",
            canonical_source_url="https://example.org/calls/1",
            deadline_at=deadline,
        )
        second = self._create_call(
            title="KOBİ Hibe Programı",
            source=self.other_source,
            official_url="https://example.org/calls/2",
            canonical_source_url="https://example.org/calls/2",
            deadline_at=deadline,
        )

        report = build_call_data_quality_report(now=self.now)

        self.assertEqual(len(report.duplicate_candidates), 1)
        self.assertEqual(set(report.duplicate_candidates[0].call_ids), {first.id, second.id})

    def test_report_ignores_same_title_for_different_institutions(self) -> None:
        deadline = self.now + timedelta(days=20)
        self._create_call(
            title="KOBI Hibe Programi",
            source=self.source,
            official_url="https://example.org/calls/1",
            canonical_source_url="https://example.org/calls/1",
            deadline_at=deadline,
        )
        self._create_call(
            title="KOBI Hibe Programi",
            source=self.other_source,
            institution=self.other_institution,
            official_url="https://example.org/calls/2",
            canonical_source_url="https://example.org/calls/2",
            deadline_at=deadline,
        )

        report = build_call_data_quality_report(now=self.now)

        self.assertEqual(report.duplicate_candidates, ())

    def test_report_flags_availability_status_mismatch(self) -> None:
        call = self._create_call(
            title="Closed call",
            source=self.source,
            official_url="https://example.org/closed",
            canonical_source_url="https://example.org/closed",
            deadline_at=self.now - timedelta(days=1),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )

        report = build_call_data_quality_report(now=self.now)

        self.assertEqual(len(report.availability_mismatches), 1)
        self.assertEqual(report.availability_mismatches[0].call_id, call.id)
        self.assertEqual(report.availability_mismatches[0].expected_status, GrantCall.AvailabilityStatus.CLOSED)

    def test_management_command_can_fail_on_issues(self) -> None:
        self._create_call(
            title="Closed call",
            source=self.source,
            official_url="https://example.org/closed",
            canonical_source_url="https://example.org/closed",
            deadline_at=self.now - timedelta(days=1),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )

        with self.assertRaises(CommandError):
            call_command("verify_call_data_quality", "--fail-on-issues", stdout=StringIO())

    def test_management_command_filters_by_source_key(self) -> None:
        self._create_call(
            title="Closed call",
            source=self.source,
            official_url="https://example.org/closed",
            canonical_source_url="https://example.org/closed",
            deadline_at=self.now - timedelta(days=1),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )

        output = StringIO()
        call_command("verify_call_data_quality", "--source-key=source-b", "--fail-on-issues", stdout=output)

        self.assertIn("Checked calls: 0", output.getvalue())
        self.assertIn("verification passed", output.getvalue())

    def test_management_command_can_require_checked_calls(self) -> None:
        with self.assertRaises(CommandError):
            call_command("verify_call_data_quality", "--source-key=source-b", "--require-checked", stdout=StringIO())

    def test_management_command_probe_rolls_back_temporary_calls(self) -> None:
        output = StringIO()

        call_command("verify_call_data_quality", "--probe", stdout=output)

        self.assertIn("Call data quality probe passed", output.getvalue())
        self.assertEqual(GrantCall.objects.count(), 0)

    def test_reject_review_calls_dry_run_does_not_update(self) -> None:
        call = self._create_call(
            title="False positive page",
            source=self.source,
            official_url="https://example.org/about",
            canonical_source_url="https://example.org/about",
            deadline_at=None,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )
        ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)
        output = StringIO()

        call_command("reject_review_calls", f"--call-id={call.id}", "--reason=false positive", stdout=output)

        call.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertIn("Dry run complete", output.getvalue())

    def test_reject_review_calls_commit_rejects_call_and_resolves_review_items(self) -> None:
        call = self._create_call(
            title="False positive page",
            source=self.source,
            official_url="https://example.org/about",
            canonical_source_url="https://example.org/about",
            deadline_at=None,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )
        review = ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)

        call_command(
            "reject_review_calls",
            f"--call-id={call.id}",
            "--reason=false positive portal page",
            "--commit",
            stdout=StringIO(),
        )

        call.refresh_from_db()
        review.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REJECTED)
        self.assertEqual(review.status, ReviewItem.Status.RESOLVED)
        self.assertEqual(review.resolution, "false positive portal page")

    def test_reject_review_calls_refuses_published_calls(self) -> None:
        call = self._create_call(
            title="Published page",
            source=self.source,
            official_url="https://example.org/published",
            canonical_source_url="https://example.org/published",
            deadline_at=self.now,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
        )

        with self.assertRaises(CommandError):
            call_command(
                "reject_review_calls",
                f"--call-id={call.id}",
                "--reason=false positive",
                "--commit",
                stdout=StringIO(),
            )

    def test_publish_review_calls_dry_run_does_not_update(self) -> None:
        call = self._create_call(
            title="Review call",
            source=self.source,
            official_url="https://example.org/review",
            canonical_source_url="https://example.org/review",
            deadline_at=self.now + timedelta(days=20),
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score=80,
        )
        output = StringIO()

        call_command("publish_review_calls", f"--call-id={call.id}", "--reason=manual review", stdout=output)

        call.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertIsNone(call.published_at)
        self.assertIn("Dry run complete", output.getvalue())

    def test_publish_review_calls_requires_explicit_missing_deadline_approval(self) -> None:
        call = self._create_call(
            title="Review call",
            source=self.source,
            official_url="https://example.org/review",
            canonical_source_url="https://example.org/review",
            deadline_at=None,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score=80,
        )

        with self.assertRaises(CommandError):
            call_command(
                "publish_review_calls",
                f"--call-id={call.id}",
                "--reason=manual review",
                "--commit",
                stdout=StringIO(),
            )

    def test_publish_review_calls_commit_publishes_call_and_resolves_review_items(self) -> None:
        call = self._create_call(
            title="Review call",
            source=self.source,
            official_url="https://example.org/review",
            canonical_source_url="https://example.org/review",
            deadline_at=None,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score=80,
        )
        review = ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT)

        call_command(
            "publish_review_calls",
            f"--call-id={call.id}",
            "--reason=manual review approved without deadline",
            "--allow-missing-deadline",
            "--commit",
            stdout=StringIO(),
        )

        call.refresh_from_db()
        review.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(call.availability_status, GrantCall.AvailabilityStatus.UNKNOWN)
        self.assertIsNotNone(call.published_at)
        self.assertEqual(review.status, ReviewItem.Status.RESOLVED)
        self.assertEqual(review.resolution, "manual review approved without deadline")

    def test_publish_review_calls_refuses_low_confidence_calls(self) -> None:
        call = self._create_call(
            title="Low confidence review call",
            source=self.source,
            official_url="https://example.org/review",
            canonical_source_url="https://example.org/review",
            deadline_at=self.now + timedelta(days=20),
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score=40,
        )

        with self.assertRaises(CommandError):
            call_command(
                "publish_review_calls",
                f"--call-id={call.id}",
                "--reason=manual review",
                "--commit",
                stdout=StringIO(),
            )

    def _create_source(self, source_key: str) -> Source:
        return Source.objects.create(
            institution=self.institution,
            source_key=source_key,
            name=source_key,
            base_url="https://example.org",
            listing_url=f"https://example.org/{source_key}",
            source_type=Source.SourceType.HTML,
            adapter_key=f"{source_key}_html_v1",
            status=Source.Status.ACTIVE,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )

    def _create_call(
        self,
        *,
        title: str,
        source: Source,
        official_url: str,
        canonical_source_url: str,
        deadline_at: datetime | None,
        institution: Institution | None = None,
        availability_status: str = GrantCall.AvailabilityStatus.OPEN,
        workflow_status: str = GrantCall.WorkflowStatus.PUBLISHED,
        confidence_score: int = 0,
    ) -> GrantCall:
        return GrantCall.objects.create(
            title=title,
            slug=f"call-{GrantCall.objects.count() + 1}",
            source=source,
            institution=institution or self.institution,
            official_url=official_url,
            canonical_source_url=canonical_source_url,
            fingerprint=f"fingerprint-{GrantCall.objects.count() + 1}",
            deadline_at=deadline_at,
            first_seen_at=self.now,
            availability_status=availability_status,
            workflow_status=workflow_status,
            confidence_score=confidence_score,
        )
