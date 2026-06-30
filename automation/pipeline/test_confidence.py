from __future__ import annotations

from datetime import UTC, datetime

from django.test import SimpleTestCase

from automation.adapters.contracts import ParsedCall, ParsedEvidence
from automation.pipeline.confidence import calculate_confidence


class ConfidenceTests(SimpleTestCase):
    def test_complete_call_can_skip_review(self) -> None:
        call = ParsedCall(
            title="Araştırma desteği",
            official_url="https://example.org/call",
            canonical_source_url="https://example.org/call",
            institution_name="Kurum",
            audience_keys=("researcher",),
            deadline_at=datetime(2026, 7, 1, tzinfo=UTC),
            summary="Özet",
            funding_text="100000 TRY",
            country_codes=("TR",),
            eligibility_text="Araştırmacılar başvurabilir.",
            evidence=(
                ParsedEvidence(field_name="title", source_url="https://example.org/call", source_excerpt="Başlık"),
            ),
        )

        decision = calculate_confidence(call)

        self.assertEqual(decision.score, 100)
        self.assertFalse(decision.requires_review)

    def test_missing_dates_force_review(self) -> None:
        call = ParsedCall(
            title="Araştırma desteği",
            official_url="https://example.org/call",
            canonical_source_url="https://example.org/call",
            institution_name="Kurum",
        )

        decision = calculate_confidence(call)

        self.assertTrue(decision.requires_review)
        self.assertIn("missing_dates", decision.reason_codes)
