from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Any

import pytest
from django.test import Client, TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, Theme


@pytest.mark.django_db
class InstitutionPublicViewTests(TestCase):
    def setUp(self) -> None:
        self.turkey = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.france = Country.objects.create(code="FR", name_tr="Fransa", name_en="France", is_europe=True)
        self.audience = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.theme = Theme.objects.create(key="yesil-donusum", name_tr="Yeşil Dönüşüm", name_en="Green Transition")
        self.institution = Institution.objects.create(
            country=self.turkey,
            name="Doğrulanmış Kurum",
            slug="dogrulanmis-kurum",
            short_name="DK",
            website_url="https://example.org",
            description="Doğrulanmış kurum açıklaması.",
            is_verified=True,
        )
        self.unverified_institution = Institution.objects.create(
            country=self.france,
            name="Doğrulanmamış Kurum",
            slug="dogrulanmamis-kurum",
            is_verified=False,
        )
        self.source = Source.objects.create(
            institution=self.institution,
            name="Kurum Kaynağı",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="kurum-calls",
        )

    def _create_call(
        self,
        *,
        title: str,
        slug: str,
        status: str,
        workflow_status: str = GrantCall.WorkflowStatus.PUBLISHED,
    ) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=self.source,
            institution=self.institution,
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"fingerprint-{slug}",
            first_seen_at=now,
            application_open_at=now,
            deadline_at=now + timedelta(days=10),
            workflow_status=workflow_status,
            availability_status=status,
            published_at=now,
        )
        call.countries.add(self.turkey)
        call.audiences.add(self.audience)
        call.themes.add(self.theme)
        return call

    def test_institution_list_shows_verified_institutions_with_call_counts(self) -> None:
        self._create_call(title="Açık Çağrı", slug="acik-cagri", status=GrantCall.AvailabilityStatus.OPEN)
        self._create_call(title="Kapalı Çağrı", slug="kapali-cagri", status=GrantCall.AvailabilityStatus.CLOSED)

        response = Client().get("/kurumlar/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doğrulanmış Kurum")
        self.assertContains(response, "Aktif açık çağrı")
        self.assertContains(response, "Toplam yayınlanmış çağrı")
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertNotIn("Doğrulanmamış Kurum", content)

    def test_institution_list_search_uses_noindex(self) -> None:
        response = Client().get("/kurumlar/", {"q": "Doğrulanmış"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doğrulanmış Kurum")
        self.assertContains(response, 'name="robots" content="noindex,follow"')

    def test_institution_detail_renders_public_data_and_calls(self) -> None:
        self._create_call(title="Açık Çağrı", slug="acik-cagri", status=GrantCall.AvailabilityStatus.OPEN)
        self._create_call(title="Kapalı Çağrı", slug="kapali-cagri", status=GrantCall.AvailabilityStatus.CLOSED)

        response = Client().get("/kurumlar/dogrulanmis-kurum/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1")
        self.assertContains(response, "Doğrulanmış kurum açıklaması.")
        self.assertContains(response, "Resmi web sitesi")
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(response, "Açık Çağrı")
        self.assertContains(response, "Kapalı Çağrı")
        self.assertContains(response, "Yeşil Dönüşüm")
        self.assertContains(response, "Veri son güncelleme")
        structured_data = _structured_data(response.content.decode())
        self.assertEqual([item["@type"] for item in structured_data], ["BreadcrumbList", "Organization"])
        self.assertEqual(structured_data[1]["name"], "DK")
        self.assertEqual(structured_data[1]["sameAs"], "https://example.org")

    def test_institution_detail_hides_unverified_institution(self) -> None:
        response = Client().get("/kurumlar/dogrulanmamis-kurum/")

        self.assertEqual(response.status_code, 404)


def _structured_data(content: str) -> list[dict[str, Any]]:
    match = re.search(r'<script[^>]+type="application/ld\+json">(.*?)</script>', content)
    if not match:
        return []
    payload = json.loads(match.group(1))
    return payload if isinstance(payload, list) else [payload]
