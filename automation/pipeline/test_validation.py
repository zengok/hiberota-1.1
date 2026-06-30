from __future__ import annotations

from datetime import UTC, datetime

from apps.ingestion.models import ReviewItem
from django.test import SimpleTestCase

from automation.adapters.contracts import ParsedCall
from automation.pipeline.validation import validate_parsed_call


class ParsedCallValidationTests(SimpleTestCase):
    def test_missing_required_urls_require_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Program",
                official_url="",
                canonical_source_url="",
            )
        )

        self.assertTrue(result.requires_review)
        self.assertEqual(
            {issue.reason_code for issue in result.issues},
            {ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD},
        )

    def test_deadline_before_application_open_requires_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Program",
                official_url="https://example.org/apply",
                canonical_source_url="https://example.org/call",
                application_open_at=datetime(2026, 7, 10, tzinfo=UTC),
                deadline_at=datetime(2026, 7, 1, tzinfo=UTC),
            )
        )

        self.assertTrue(result.requires_review)
        self.assertIn(ReviewItem.ReasonCode.DEADLINE_CONFLICT, {issue.reason_code for issue in result.issues})

    def test_portal_source_category_requires_detail_discovery_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Programme portal",
                official_url="https://example.org/funding",
                canonical_source_url="https://example.org/funding",
                raw_metadata={"source_category": "programme_portal"},
            )
        )

        self.assertTrue(result.requires_review)
        self.assertIn(ReviewItem.ReasonCode.SOURCE_RESTRICTED, {issue.reason_code for issue in result.issues})

    def test_portal_detail_item_does_not_require_source_restricted_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Open call",
                official_url="https://example.org/funding/open-call",
                canonical_source_url="https://example.org/funding/open-call",
                raw_metadata={"source_category": "programme_portal", "item_kind": "detail"},
            )
        )

        self.assertNotIn(ReviewItem.ReasonCode.SOURCE_RESTRICTED, {issue.reason_code for issue in result.issues})

    def test_closed_source_status_requires_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Closed call",
                official_url="https://example.org/funding/closed-call",
                canonical_source_url="https://example.org/funding/closed-call",
                raw_metadata={"source_status": "closed", "source_category": "agency_portal", "item_kind": "detail"},
            )
        )

        self.assertTrue(result.requires_review)
        self.assertIn(ReviewItem.ReasonCode.SOURCE_RESTRICTED, {issue.reason_code for issue in result.issues})

    def test_any_portal_suffix_listing_requires_detail_discovery_review(self) -> None:
        result = validate_parsed_call(
            ParsedCall(
                title="Foundation portal",
                official_url="https://example.org/grants",
                canonical_source_url="https://example.org/grants",
                raw_metadata={"source_category": "foundation_portal"},
            )
        )

        self.assertIn(ReviewItem.ReasonCode.SOURCE_RESTRICTED, {issue.reason_code for issue in result.issues})
