from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.calls.fingerprints import build_duplicate_fingerprint
from apps.calls.models import GrantCall
from apps.institutions.models import Country
from apps.sources.models import Source


class DomainModelTests(TestCase):
    def test_country_code_requires_iso_alpha_2_shape(self) -> None:
        country = Country(code="TUR", name_tr="Türkiye", name_en="Turkey")

        with self.assertRaises(ValidationError):
            country.full_clean()

    def test_source_type_rejects_unknown_value(self) -> None:
        allowed_values = {choice.value for choice in Source.SourceType}

        self.assertIn("html", allowed_values)
        self.assertNotIn("agency_portal", allowed_values)

    def test_duplicate_fingerprint_normalizes_title_case_and_accents(self) -> None:
        deadline = timezone.now()

        first = build_duplicate_fingerprint(
            institution_id=1,
            title="TÜBİTAK KOBİ Destek Çağrısı!",
            deadline_at=deadline,
            canonical_source_url="HTTPS://EXAMPLE.ORG/CALL",
        )
        second = build_duplicate_fingerprint(
            institution_id=1,
            title="tubitak kobi destek cagrisi",
            deadline_at=deadline,
            canonical_source_url="https://example.org/call",
        )

        self.assertEqual(first, second)

    def test_duplicate_fingerprint_is_semantic_not_canonical_url_based(self) -> None:
        deadline = timezone.now()

        first = build_duplicate_fingerprint(
            institution_id=1,
            title="KOBI Hibe Programi",
            deadline_at=deadline,
            canonical_source_url="https://example.org/call-a",
        )
        second = build_duplicate_fingerprint(
            institution_id=1,
            title="KOBI Hibe Programi",
            deadline_at=deadline,
            canonical_source_url="https://example.org/call-b",
        )

        self.assertEqual(first, second)

    def test_grant_call_rejects_invalid_funding_range(self) -> None:
        call = GrantCall(funding_min=Decimal("200.00"), funding_max=Decimal("100.00"))

        with self.assertRaises(ValidationError):
            call.validate_constraints()
