from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import Client, TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, Sector


@pytest.mark.django_db
class GrantSurveyViewTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.student = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.sme = AudienceType.objects.create(key="kobi", name_tr="KOBİ", name_en="SME")
        self.energy = Sector.objects.create(key="enerji", name_tr="Enerji", name_en="Energy")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")
        self.source = Source.objects.create(
            institution=self.institution,
            name="Kaynak",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="survey-view-source",
        )

    def _create_call(self, *, title: str, slug: str, audience: AudienceType) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=self.source,
            institution=self.institution,
            summary=f"{title} enerji desteği",
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"fingerprint-{slug}",
            first_seen_at=now,
            application_open_at=now,
            deadline_at=now + timedelta(days=20),
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            published_at=now,
        )
        call.countries.add(self.country)
        call.audiences.add(audience)
        call.sectors.add(self.energy)
        return call

    def test_survey_page_is_public_noindex_without_account_language(self) -> None:
        response = Client().get("/hibe-anketi/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hibe Anketi")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, 'aria-live="polite"')
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_survey_post_returns_matching_calls_only(self) -> None:
        student_call = self._create_call(title="Öğrenci Enerji Desteği", slug="ogrenci-enerji", audience=self.student)
        self._create_call(title="KOBİ Enerji Desteği", slug="kobi-enerji", audience=self.sme)

        response = Client().post(
            "/hibe-anketi/",
            {
                "q": "enerji",
                "audience": str(self.student.id),
                "sector": str(self.energy.id),
                "country": str(self.country.id),
                "availability_status": GrantCall.AvailabilityStatus.OPEN,
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Öğrenci Enerji Desteği")
        self.assertContains(response, f"/cagrilar/{student_call.slug}-{student_call.id}/")
        self.assertNotIn("KOBİ Enerji Desteği", content)

    def test_survey_requires_audience(self) -> None:
        response = Client().post("/hibe-anketi/", {"q": "enerji"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu alan zorunludur.")
