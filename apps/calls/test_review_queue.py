from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.calls.review_queue import ReviewQueueCategory, build_review_queue_report
from apps.ingestion.models import FieldEvidence, ReviewItem
from apps.institutions.models import Country, Institution
from apps.sources.models import Source


class ReviewQueueReportTests(TestCase):
    def setUp(self) -> None:
        self.now = timezone.now()
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")
        self.source = Source.objects.create(
            institution=self.institution,
            source_key="source-a",
            name="Source A",
            base_url="https://example.org",
            listing_url="https://example.org/funding",
            source_type=Source.SourceType.HTML,
            adapter_key="source_a_html_v1",
            status=Source.Status.ACTIVE,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )

    def test_report_classifies_review_calls_by_operator_action(self) -> None:
        closed = self._create_review_call(
            title="Closed funding call",
            url="https://example.org/funding/closed",
            deadline_at=self.now + timedelta(days=20),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=80,
        )
        FieldEvidence.objects.create(
            grant_call=closed,
            source=self.source,
            field_name="source_status",
            source_url=closed.canonical_source_url,
            source_excerpt="Closed",
            fetched_at=self.now,
            content_hash="closed-hash",
            parser_version="test",
            confidence=90,
        )
        ReviewItem.objects.create(grant_call=closed, reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED)

        guidance = self._create_review_call(
            title="Applying for funding",
            url="https://example.org/funding/applying",
            deadline_at=None,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            confidence_score=70,
        )
        ReviewItem.objects.create(grant_call=guidance, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)

        publish_candidate = self._create_review_call(
            title="Open climate fund",
            url="https://example.org/funding/open-climate-fund",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        ReviewItem.objects.create(
            grant_call=publish_candidate,
            reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE,
        )

        manual = self._create_review_call(
            title="Deadline needs checking",
            url="https://example.org/funding/deadline-check",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        ReviewItem.objects.create(grant_call=manual, reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT)

        report = build_review_queue_report(now=self.now)

        categories = {entry.call.id: entry.category for entry in report.entries}
        self.assertEqual(categories[closed.id], ReviewQueueCategory.CLOSED_SOURCE)
        self.assertEqual(categories[guidance.id], ReviewQueueCategory.GUIDANCE_PAGE)
        self.assertEqual(categories[publish_candidate.id], ReviewQueueCategory.PUBLISH_CANDIDATE)
        self.assertEqual(categories[manual.id], ReviewQueueCategory.NEEDS_MANUAL_REVIEW)
        self.assertEqual(report.counts_by_category()[ReviewQueueCategory.PUBLISH_CANDIDATE], 1)

    def test_management_command_prints_category_summary(self) -> None:
        call = self._create_review_call(
            title="Open climate fund",
            url="https://example.org/funding/open-climate-fund",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)
        output = StringIO()

        call_command("report_review_queue", "--category=publish_candidate", stdout=output)

        value = output.getvalue()
        self.assertIn("Review queue summary", value)
        self.assertIn("- publish_candidate: 1", value)
        self.assertIn("Open climate fund", value)
        self.assertIn("only low-confidence review remains", value)

    def _create_review_call(
        self,
        *,
        title: str,
        url: str,
        deadline_at: datetime | None,
        availability_status: str,
        confidence_score: int,
    ) -> GrantCall:
        count = GrantCall.objects.count() + 1
        return GrantCall.objects.create(
            title=title,
            slug=f"review-call-{count}",
            source=self.source,
            institution=self.institution,
            official_url=url,
            canonical_source_url=url,
            fingerprint=f"review-fingerprint-{count}",
            deadline_at=deadline_at,
            first_seen_at=self.now,
            availability_status=availability_status,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
            confidence_score=confidence_score,
        )
