from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.calls.admin import ADMIN_PUBLISH_REASON, ADMIN_REJECT_REASON, GrantCallAdmin
from apps.calls.models import GrantCall
from apps.ingestion.models import ReviewItem
from apps.institutions.models import Country, Institution
from apps.sources.models import Source


class GrantCallAdminTests(TestCase):
    def setUp(self) -> None:
        self.now = timezone.now()
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.institution = Institution.objects.create(
            country=self.country,
            name="Kurum",
            slug="kurum",
            is_verified=True,
        )
        self.source = Source.objects.create(
            institution=self.institution,
            source_key="source-a",
            name="Source A",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="source_a_html_v1",
        )
        self.model_admin = admin.site._registry[GrantCall]

    def test_grant_call_admin_exposes_review_actions(self) -> None:
        self.assertIsInstance(self.model_admin, GrantCallAdmin)
        self.assertIn("publish_review_candidates", self.model_admin.actions)
        self.assertIn("reject_review_calls", self.model_admin.actions)

    def test_publish_review_candidates_publishes_only_safe_review_calls(self) -> None:
        eligible = self._create_call(
            title="Eligible review call",
            deadline_at=self.now + timedelta(days=20),
            confidence_score=80,
        )
        eligible_review = ReviewItem.objects.create(
            grant_call=eligible,
            reason_code=ReviewItem.ReasonCode.LOW_CONFIDENCE,
        )
        blocked = self._create_call(
            title="Blocked review call",
            deadline_at=self.now + timedelta(days=20),
            confidence_score=80,
        )
        blocked_review = ReviewItem.objects.create(
            grant_call=blocked,
            reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
        )
        low_confidence = self._create_call(
            title="Low confidence review call",
            deadline_at=self.now + timedelta(days=20),
            confidence_score=40,
        )
        missing_deadline = self._create_call(
            title="Missing deadline review call",
            deadline_at=None,
            confidence_score=80,
        )

        queryset = GrantCall.objects.filter(id__in=[eligible.id, blocked.id, low_confidence.id, missing_deadline.id])

        self.model_admin.publish_review_candidates(self._request(), queryset)

        eligible.refresh_from_db()
        eligible_review.refresh_from_db()
        blocked.refresh_from_db()
        blocked_review.refresh_from_db()
        low_confidence.refresh_from_db()
        missing_deadline.refresh_from_db()
        self.assertEqual(eligible.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertIsNotNone(eligible.published_at)
        self.assertEqual(eligible_review.status, ReviewItem.Status.RESOLVED)
        self.assertEqual(eligible_review.resolution, ADMIN_PUBLISH_REASON)
        self.assertEqual(blocked.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertEqual(blocked_review.status, ReviewItem.Status.OPEN)
        self.assertEqual(low_confidence.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        self.assertEqual(missing_deadline.workflow_status, GrantCall.WorkflowStatus.REVIEW)

    def test_reject_review_calls_rejects_only_review_calls(self) -> None:
        review_call = self._create_call(
            title="Review call",
            deadline_at=self.now + timedelta(days=20),
            confidence_score=80,
        )
        review_item = ReviewItem.objects.create(
            grant_call=review_call,
            reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
        )
        published_call = self._create_call(
            title="Published call",
            deadline_at=self.now + timedelta(days=20),
            confidence_score=80,
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
        )

        queryset = GrantCall.objects.filter(id__in=[review_call.id, published_call.id])

        self.model_admin.reject_review_calls(self._request(), queryset)

        review_call.refresh_from_db()
        review_item.refresh_from_db()
        published_call.refresh_from_db()
        self.assertEqual(review_call.workflow_status, GrantCall.WorkflowStatus.REJECTED)
        self.assertEqual(review_item.status, ReviewItem.Status.RESOLVED)
        self.assertEqual(review_item.resolution, ADMIN_REJECT_REASON)
        self.assertEqual(published_call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)

    def _create_call(
        self,
        *,
        title: str,
        deadline_at: datetime | None,
        confidence_score: int,
        workflow_status: str = GrantCall.WorkflowStatus.REVIEW,
    ) -> GrantCall:
        count = GrantCall.objects.count() + 1
        return GrantCall.objects.create(
            title=title,
            slug=f"call-{count}",
            source=self.source,
            institution=self.institution,
            official_url=f"https://example.org/calls/{count}",
            canonical_source_url=f"https://example.org/calls/{count}",
            fingerprint=f"fingerprint-{count}",
            first_seen_at=self.now,
            deadline_at=deadline_at,
            workflow_status=workflow_status,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            confidence_score=confidence_score,
        )

    def _request(self):
        request = RequestFactory().post("/admin/calls/grantcall/")
        request.session = {}
        request._messages = FallbackStorage(request)  # type: ignore[attr-defined]
        return request
