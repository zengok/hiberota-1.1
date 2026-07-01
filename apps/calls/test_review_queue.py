from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

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

    def test_reject_review_queue_category_dry_run_does_not_update(self) -> None:
        call = self._create_review_call(
            title="Applying for funding",
            url="https://example.org/funding/applying",
            deadline_at=None,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            confidence_score=70,
        )
        ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)
        output = StringIO()

        call_command("reject_review_queue_category", "--category=guidance_page", stdout=output)

        call.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertIn("Matched 1 guidance_page review calls", output.getvalue())
        self.assertIn("Dry run complete", output.getvalue())

    def test_reject_review_queue_category_commit_rejects_safe_category(self) -> None:
        call = self._create_review_call(
            title="Applying for funding",
            url="https://example.org/funding/applying",
            deadline_at=None,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            confidence_score=70,
        )
        review = ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)

        call_command("reject_review_queue_category", "--category=guidance_page", "--commit", stdout=StringIO())

        call.refresh_from_db()
        review.refresh_from_db()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REJECTED)
        self.assertEqual(review.status, ReviewItem.Status.RESOLVED)
        self.assertIn("guidance", review.resolution)

    def test_reject_review_queue_category_refuses_manual_review_category(self) -> None:
        with self.assertRaises(CommandError):
            call_command("reject_review_queue_category", "--category=needs_manual_review", stdout=StringIO())

    def test_report_classifies_turkish_listing_pages_as_guidance(self) -> None:
        call = self._create_review_call(
            title="Destek ve Duyurular",
            url="https://example.org/destek-ve-duyurular",
            deadline_at=None,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            confidence_score=70,
        )
        ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)

        report = build_review_queue_report(now=self.now)

        self.assertEqual(report.entries[0].category, ReviewQueueCategory.GUIDANCE_PAGE)

    def test_report_classifies_turkish_non_call_announcements_as_guidance(self) -> None:
        titles = [
            "İhale İlanları",
            "Ana Sayfa",
            "2026 Yılı Teknik Destek Programı Mart-Nisan Dönemi Değerlendirme Sonuçları",
            "Proje Uygulama Dokümanları",
        ]
        for title in titles:
            call = self._create_review_call(
                title=title,
                url=f"https://example.org/{slugify(title)}",
                deadline_at=None,
                availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
                confidence_score=70,
            )
            ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)

        report = build_review_queue_report(now=self.now)

        self.assertEqual(
            {entry.call.title: entry.category for entry in report.entries},
            {title: ReviewQueueCategory.GUIDANCE_PAGE for title in titles},
        )

    def test_publish_regional_review_calls_publishes_safe_turkey_and_europe_candidates(self) -> None:
        europe_country = Country.objects.create(code="DE", name_tr="Almanya", name_en="Germany", is_europe=True)
        other_country = Country.objects.create(code="US", name_tr="ABD", name_en="United States", is_europe=False)
        europe_institution = Institution.objects.create(country=europe_country, name="EU Kurum", slug="eu-kurum")
        other_institution = Institution.objects.create(country=other_country, name="US Kurum", slug="us-kurum")
        europe_source = Source.objects.create(
            institution=europe_institution,
            source_key="source-de",
            name="DE Source",
            base_url="https://de.example.org",
            listing_url="https://de.example.org/funding",
            source_type=Source.SourceType.HTML,
            adapter_key="source_de_html_v1",
            status=Source.Status.ACTIVE,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )
        other_source = Source.objects.create(
            institution=other_institution,
            source_key="source-us",
            name="US Source",
            base_url="https://us.example.org",
            listing_url="https://us.example.org/funding",
            source_type=Source.SourceType.HTML,
            adapter_key="source_us_html_v1",
            status=Source.Status.ACTIVE,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )
        turkey = self._create_review_call(
            title="Yeşil dönüşüm çağrısı",
            url="https://example.org/funding/green-transition",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        europe = self._create_review_call(
            title="European innovation fund",
            url="https://de.example.org/funding/innovation",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        europe.source = europe_source
        europe.institution = europe_institution
        europe.save(update_fields=["source", "institution", "updated_at"])
        other = self._create_review_call(
            title="US innovation fund",
            url="https://us.example.org/funding/innovation",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        other.source = other_source
        other.institution = other_institution
        other.save(update_fields=["source", "institution", "updated_at"])
        guidance = self._create_review_call(
            title="Duyurular",
            url="https://example.org/duyurular",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=75,
        )
        blocked = self._create_review_call(
            title="Takvim çakışması",
            url="https://example.org/funding/conflict",
            deadline_at=self.now + timedelta(days=30),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=90,
        )
        for call in (turkey, europe, other, guidance):
            ReviewItem.objects.create(grant_call=call, reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE)
        ReviewItem.objects.create(grant_call=blocked, reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT)

        call_command("publish_regional_review_calls", "--region=tr-europe", "--commit", stdout=StringIO())

        turkey.refresh_from_db()
        europe.refresh_from_db()
        other.refresh_from_db()
        guidance.refresh_from_db()
        blocked.refresh_from_db()
        self.assertEqual(turkey.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(europe.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(other.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertEqual(guidance.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertEqual(blocked.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertFalse(
            ReviewItem.objects.filter(
                grant_call__in=(turkey, europe),
                status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS),
            ).exists()
        )

    def test_normalize_review_reason_codes_resolves_only_false_deadline_conflicts(self) -> None:
        false_conflict = self._create_review_call(
            title="Missing date review",
            url="https://example.org/funding/missing-date",
            deadline_at=None,
            availability_status=GrantCall.AvailabilityStatus.UNKNOWN,
            confidence_score=70,
        )
        false_review = ReviewItem.objects.create(
            grant_call=false_conflict,
            reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
        )
        real_conflict = self._create_review_call(
            title="Real date conflict",
            url="https://example.org/funding/real-conflict",
            deadline_at=self.now + timedelta(days=1),
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=90,
        )
        real_conflict.application_open_at = self.now + timedelta(days=10)
        real_conflict.save(update_fields=["application_open_at", "updated_at"])
        real_review = ReviewItem.objects.create(
            grant_call=real_conflict,
            reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
        )

        call_command("normalize_review_reason_codes", "--commit", stdout=StringIO())

        false_review.refresh_from_db()
        real_review.refresh_from_db()
        self.assertEqual(false_review.status, ReviewItem.Status.RESOLVED)
        self.assertEqual(real_review.status, ReviewItem.Status.OPEN)
        self.assertTrue(
            ReviewItem.objects.filter(
                grant_call=false_conflict,
                reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE,
                status=ReviewItem.Status.OPEN,
            ).exists()
        )

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
