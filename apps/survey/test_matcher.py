from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.survey.matcher import SurveyProfile, match_calls
from apps.taxonomy.models import AudienceType, Sector


@pytest.mark.django_db
class TestSurveyMatcher(TestCase):
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
            adapter_key="survey-source",
        )

    def _create_call(self, *, title: str, slug: str, audience: AudienceType) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=self.source,
            institution=self.institution,
            summary=f"{title} enerji araştırma desteği",
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"fingerprint-{slug}",
            first_seen_at=now,
            application_open_at=now,
            deadline_at=now + timedelta(days=30),
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            published_at=now,
        )
        call.countries.add(self.country)
        call.audiences.add(audience)
        call.sectors.add(self.energy)
        return call

    def test_matcher_hard_filters_by_audience_before_scoring(self) -> None:
        student_call = self._create_call(title="Öğrenci Enerji Programı", slug="ogrenci-enerji", audience=self.student)
        self._create_call(title="KOBİ Enerji Programı", slug="kobi-enerji", audience=self.sme)

        matches = match_calls(SurveyProfile(query="enerji", audience=self.student, sector=self.energy))

        self.assertEqual([match.call.id for match in matches], [student_call.id])
        self.assertIn("Hedef kitle uyumlu", matches[0].reasons[0])

    def test_matcher_ignores_closed_calls_by_default(self) -> None:
        open_call = self._create_call(title="Açık Program", slug="acik-program", audience=self.student)
        closed_call = self._create_call(title="Kapalı Program", slug="kapali-program", audience=self.student)
        closed_call.availability_status = GrantCall.AvailabilityStatus.CLOSED
        closed_call.save()

        matches = match_calls(SurveyProfile(query="program", audience=self.student))

        self.assertEqual([match.call.id for match in matches], [open_call.id])
