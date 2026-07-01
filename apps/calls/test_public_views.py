from __future__ import annotations

import json
import re
from datetime import timedelta
from html.parser import HTMLParser
from typing import Any

import pytest
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from apps.calls import embed as embed_module
from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType, Sector


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "id" and value:
                self.ids.append(value)


@pytest.mark.django_db
class CallListViewTests(TestCase):
    def setUp(self) -> None:
        self.turkey = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey", region_code="europe")
        self.france = Country.objects.create(
            code="FR",
            name_tr="Fransa",
            name_en="France",
            region_code="europe",
            is_europe=True,
        )
        self.student = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.sme = AudienceType.objects.create(key="kobi", name_tr="KOBİ", name_en="SME")
        self.energy = Sector.objects.create(key="enerji", name_tr="Enerji", name_en="Energy")
        self.institution = Institution.objects.create(
            country=self.turkey,
            name="Türkiye Kurumu",
            slug="turkiye-kurumu",
            is_verified=True,
        )
        self.world_institution = Institution.objects.create(
            country=self.france,
            name="Avrupa Kurumu",
            slug="avrupa-kurumu",
            is_verified=True,
        )
        self.source = Source.objects.create(
            institution=self.institution,
            name="Türkiye Kaynağı",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="turkiye-calls",
        )
        self.world_source = Source.objects.create(
            institution=self.world_institution,
            name="Avrupa Kaynağı",
            base_url="https://eu.example.org",
            listing_url="https://eu.example.org/calls",
            source_type=Source.SourceType.FEED,
            adapter_key="avrupa-calls",
        )

    def _create_call(
        self,
        *,
        title: str,
        slug: str,
        source: Source,
        institution: Institution,
        country: Country,
        audience: AudienceType,
        first_seen_offset_days: int = 0,
        deadline_offset_days: int = 15,
        status: str = GrantCall.AvailabilityStatus.OPEN,
        workflow_status: str = GrantCall.WorkflowStatus.PUBLISHED,
        currency: str = "EUR",
    ) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=source,
            institution=institution,
            summary=f"{title} özeti",
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"fingerprint-{slug}",
            first_seen_at=now + timedelta(days=first_seen_offset_days),
            application_open_at=now + timedelta(days=first_seen_offset_days),
            deadline_at=now + timedelta(days=deadline_offset_days),
            currency=currency,
            workflow_status=workflow_status,
            availability_status=status,
            published_at=now + timedelta(days=first_seen_offset_days),
        )
        call.countries.add(country)
        call.audiences.add(audience)
        call.sectors.add(self.energy)
        return call

    def test_call_list_shows_only_published_calls_by_default(self) -> None:
        self._create_call(
            title="Yayınlanmış Türkiye Çağrısı",
            slug="yayinlanmis-turkiye-cagrisi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )
        self._create_call(
            title="İncelemedeki Çağrı",
            slug="incelemedeki-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )

        response = Client().get("/cagrilar/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hibe ve fon çağrıları")
        self.assertContains(response, "1 sonuç")
        self.assertContains(response, "Yayınlanmış Türkiye Çağrısı")
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertNotIn("adsbygoogle", content)
        self.assertNotIn("pagead2.googlesyndication.com", content)
        self.assertNotIn("İncelemedeki Çağrı", content)

    def test_call_list_explains_missing_deadline_for_published_call(self) -> None:
        call = self._create_call(
            title="Tarihi Belirsiz Çağrı",
            slug="tarihi-belirsiz-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            status=GrantCall.AvailabilityStatus.UNKNOWN,
        )
        call.deadline_at = None
        call.save(update_fields=["deadline_at", "updated_at"])

        response = Client().get("/cagrilar/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tarihi Belirsiz Çağrı")
        self.assertContains(response, "Resmi kaynakta tarih belirtilmemiş")
        self.assertContains(response, "Tarih belirtilmemiş")

    @override_settings(
        ADSENSE_ENABLED=True,
        ADSENSE_CLIENT_ID="ca-pub-1234567890123456",
        ADSENSE_SLOT_CALL_LIST_TOP="1111222233",
    )
    def test_call_list_renders_ad_slot_only_when_adsense_identity_exists(self) -> None:
        self._create_call(
            title="Reklam Slotlu Çağrı",
            slug="reklam-slotlu-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get("/cagrilar/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="adsbygoogle"')
        self.assertContains(response, 'data-ad-client="ca-pub-1234567890123456"')
        self.assertContains(response, 'data-ad-slot="1111222233"')
        self.assertNotIn("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js", content)

    def test_call_list_filters_by_query_country_audience_status_and_currency(self) -> None:
        self._create_call(
            title="Öğrenci Enerji Desteği",
            slug="ogrenci-enerji-destegi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            status=GrantCall.AvailabilityStatus.CLOSING_SOON,
            currency="TRY",
        )
        self._create_call(
            title="KOBİ Avrupa Programı",
            slug="kobi-avrupa-programi",
            source=self.world_source,
            institution=self.world_institution,
            country=self.france,
            audience=self.sme,
            currency="EUR",
        )

        response = Client().get(
            "/cagrilar/",
            {
                "q": "Enerji",
                "ulke": "TR",
                "hedef": "ogrenci",
                "durum": GrantCall.AvailabilityStatus.CLOSING_SOON,
                "para_birimi": "TRY",
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Öğrenci Enerji Desteği")
        self.assertContains(response, "Arama: Enerji")
        self.assertContains(response, "Durum: Kapanmak üzere")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertNotIn("KOBİ Avrupa Programı", content)

    def test_call_list_filters_world_scope_outside_turkey(self) -> None:
        self._create_call(
            title="Türkiye Programı",
            slug="turkiye-programi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )
        self._create_call(
            title="Avrupa Programı",
            slug="avrupa-programi",
            source=self.world_source,
            institution=self.world_institution,
            country=self.france,
            audience=self.sme,
        )

        response = Client().get("/cagrilar/", {"kapsam": "dunya"})
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Avrupa Programı")
        self.assertContains(response, "Kapsam: Dünya")
        self.assertNotIn("Türkiye Programı", content)

    def test_call_list_filters_by_multiple_audiences(self) -> None:
        student = AudienceType.objects.create(key="student", name_tr="Öğrenci", name_en="Student")
        sme = AudienceType.objects.create(key="sme", name_tr="KOBİ", name_en="SME")
        self._create_call(
            title="Öğrenci Programı",
            slug="ogrenci-programi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=student,
        )
        self._create_call(
            title="KOBİ Programı",
            slug="kobi-programi",
            source=self.world_source,
            institution=self.world_institution,
            country=self.france,
            audience=sme,
        )

        response = Client().get("/cagrilar/", {"hedef": ["student", "sme"]})
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Öğrenci Programı")
        self.assertContains(response, "KOBİ Programı")
        self.assertContains(response, "Hedef kitle: Öğrenci, KOBİ")
        self.assertNotIn("2 sonuç bulunamadı", content)

    def test_call_list_mobile_filter_controls_are_accessible(self) -> None:
        response = Client().get("/cagrilar/", {"q": "bulunmayacak"})
        content = response.content.decode()
        parser = IdCollector()
        parser.feed(content)

        self.assertContains(response, 'id="call-results-count" aria-live="polite"')
        self.assertContains(response, 'aria-controls="callFilterOffcanvas"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'aria-describedby="call-results-count"', count=2)
        self.assertContains(response, "Tüm filtreleri temizle")
        self.assertContains(response, 'data-bs-dismiss="offcanvas"')
        self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_call_list_sorting_preserves_filters(self) -> None:
        self._create_call(
            title="Eski Çağrı",
            slug="eski-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            first_seen_offset_days=-5,
        )
        self._create_call(
            title="Yeni Çağrı",
            slug="yeni-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get("/cagrilar/", {"ulke": "TR", "siralama": "eski"})
        content = response.content.decode()

        self.assertLess(content.index("Eski Çağrı"), content.index("Yeni Çağrı"))
        self.assertContains(response, 'type="hidden" name="ulke" value="TR"')

    def test_call_list_prioritizes_live_calls_before_unknown_and_closed(self) -> None:
        self._create_call(
            title="Kapalı Çağrı",
            slug="kapali-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            first_seen_offset_days=3,
            status=GrantCall.AvailabilityStatus.CLOSED,
        )
        self._create_call(
            title="Tarihi Belirsiz Çağrı",
            slug="tarihi-belirsiz-cagri-siralama",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            first_seen_offset_days=2,
            status=GrantCall.AvailabilityStatus.UNKNOWN,
        )
        self._create_call(
            title="Açık Çağrı",
            slug="acik-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            first_seen_offset_days=-1,
            status=GrantCall.AvailabilityStatus.OPEN,
        )

        response = Client().get("/cagrilar/")
        content = response.content.decode()

        self.assertLess(content.index("Açık Çağrı"), content.index("Tarihi Belirsiz Çağrı"))
        self.assertLess(content.index("Tarihi Belirsiz Çağrı"), content.index("Kapalı Çağrı"))

    def test_call_cards_render_deadline_badges_favorite_heart_and_verify_footer(self) -> None:
        self._create_call(
            title="Acil Çağrı",
            slug="acil-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            deadline_offset_days=4,
        )
        self._create_call(
            title="Açık Çağrı",
            slug="acik-cagri-kart",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            deadline_offset_days=20,
        )
        self._create_call(
            title="Kapalı Çağrı",
            slug="kapali-cagri-kart",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            deadline_offset_days=-1,
            status=GrantCall.AvailabilityStatus.CLOSED,
        )

        response = Client().get("/cagrilar/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="deadline-status-badge deadline-status-badge--urgent">4 gün kaldı</span>')
        self.assertContains(response, 'class="deadline-status-badge deadline-status-badge--open">Açık · 20 gün</span>')
        self.assertContains(response, 'class="call-card call-card--closed"')
        self.assertContains(response, 'class="deadline-status-badge deadline-status-badge--closed">Kapalı</span>')
        self.assertContains(response, "favorite-toggle__icon favorite-toggle__icon--outline")
        self.assertContains(response, "favorite-toggle__icon favorite-toggle__icon--filled")
        self.assertContains(response, 'class="call-card__verify"')
        self.assertNotIn("status-badge status-badge--open", content)

    def test_call_detail_renders_published_call_with_source_links(self) -> None:
        call = self._create_call(
            title="Detaylı Hibe Çağrısı",
            slug="detayli-hibe-cagrisi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )
        call.purpose = "Programın amacı sürdürülebilir projeleri desteklemektir."
        call.eligibility_text = "Öğrenciler ve araştırmacılar başvurabilir."
        call.application_process_text = "Başvuru resmi kaynak üzerinden yapılır."
        call.save()

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1")
        self.assertContains(response, "Detaylı Hibe Çağrısı")
        self.assertContains(response, "Resmi başvuru")
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertContains(response, f"/cagrilar/{call.slug}-{call.id}/")
        self.assertContains(response, 'property="og:type" content="website"')
        self.assertContains(response, f'property="og:url" content="http://testserver/cagrilar/{call.slug}-{call.id}/"')
        self.assertContains(response, 'data-share-url="http://testserver/cagrilar/')
        self.assertContains(response, "/static/js/share.js")
        self.assertNotIn("adsbygoogle", response.content.decode())
        self.assertContains(response, "Veri kaynağı")
        structured_data = _structured_data(response.content.decode())
        self.assertEqual(structured_data[0]["@type"], "BreadcrumbList")
        self.assertEqual(
            [item["name"] for item in structured_data[0]["itemListElement"]],
            ["Ana Sayfa", "Çağrılar", "Detaylı Hibe Çağrısı"],
        )

    def test_call_detail_explains_missing_deadline(self) -> None:
        call = self._create_call(
            title="Detay Tarihi Belirsiz Çağrı",
            slug="detay-tarihi-belirsiz-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            status=GrantCall.AvailabilityStatus.UNKNOWN,
        )
        call.deadline_at = None
        call.save(update_fields=["deadline_at", "updated_at"])

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resmi kaynakta son başvuru tarihi belirtilmemiş")
        self.assertContains(response, "Başvuru yapmadan önce resmi sayfayı kontrol edin")
        self.assertContains(response, "Tarih belirtilmemiş")

    def test_call_detail_redirects_wrong_slug_to_canonical_url(self) -> None:
        call = self._create_call(
            title="Canonical Çağrı",
            slug="canonical-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get(f"/cagrilar/yanlis-slug-{call.id}/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"/cagrilar/{call.slug}-{call.id}/")

    def test_call_detail_hides_unpublished_call(self) -> None:
        call = self._create_call(
            title="Public Olmayan Çağrı",
            slug="public-olmayan-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/")

        self.assertEqual(response.status_code, 404)

    def test_call_detail_returns_410_for_archived_call(self) -> None:
        call = self._create_call(
            title="Arşivlenmiş Çağrı",
            slug="arsivlenmis-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            workflow_status=GrantCall.WorkflowStatus.ARCHIVED,
        )

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 410)
        self.assertContains(response, "Bu kayıt yayından kaldırıldı", status_code=410)
        self.assertContains(response, 'name="robots" content="noindex,follow"', status_code=410)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_call_embed_renders_safe_read_only_badge(self) -> None:
        call = self._create_call(
            title="Embed Hibe Çağrısı",
            slug="embed-hibe-cagrisi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/embed/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HibeRota çağrı kartı")
        self.assertContains(response, "Embed Hibe Çağrısı")
        self.assertContains(response, "HibeRota'da görüntüle")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, f"http://testserver/cagrilar/{call.slug}-{call.id}/")
        self.assertIn("default-src 'none'", response["Content-Security-Policy"])
        self.assertIn("frame-ancestors", response["Content-Security-Policy"])
        self.assertNotIn("Cross-Origin-Resource-Policy", response)
        self.assertNotIn("X-Frame-Options", response)
        self.assertNotIn("<script", content)
        self.assertNotIn("<form", content)
        self.assertNotIn("localStorage", content)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_call_embed_explains_missing_deadline(self) -> None:
        call = self._create_call(
            title="Embed Tarihi Belirsiz Çağrı",
            slug="embed-tarihi-belirsiz-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            status=GrantCall.AvailabilityStatus.UNKNOWN,
        )
        call.deadline_at = None
        call.save(update_fields=["deadline_at", "updated_at"])

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/embed/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resmi kaynakta tarih belirtilmemiş")
        self.assertContains(response, "Tarih belirtilmemiş")

    def test_call_embed_redirects_wrong_slug_to_canonical_embed_url(self) -> None:
        call = self._create_call(
            title="Embed Canonical Çağrı",
            slug="embed-canonical-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get(f"/cagrilar/yanlis-slug-{call.id}/embed/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"/cagrilar/{call.slug}-{call.id}/embed/")

    def test_call_embed_hides_unpublished_call(self) -> None:
        call = self._create_call(
            title="Embed Gizli Çağrı",
            slug="embed-gizli-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )

        response = Client().get(f"/cagrilar/{call.slug}-{call.id}/embed/")

        self.assertEqual(response.status_code, 404)

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_call_embed_rate_limit_returns_plain_429(self) -> None:
        call = self._create_call(
            title="Embed Limit Çağrısı",
            slug="embed-limit-cagrisi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )
        original_limit = embed_module.EMBED_RATE_LIMIT
        embed_module.EMBED_RATE_LIMIT = 1
        try:
            client = Client(REMOTE_ADDR="203.0.113.10")
            self.assertEqual(client.get(f"/cagrilar/{call.slug}-{call.id}/embed/").status_code, 200)
            response = client.get(f"/cagrilar/{call.slug}-{call.id}/embed/")
        finally:
            embed_module.EMBED_RATE_LIMIT = original_limit

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(response.content.decode(), "Too many requests")

    def test_favorite_resolve_returns_only_published_calls_in_requested_order(self) -> None:
        first_call = self._create_call(
            title="İlk Favori",
            slug="ilk-favori",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )
        hidden_call = self._create_call(
            title="Gizli Favori",
            slug="gizli-favori",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )
        second_call = self._create_call(
            title="İkinci Favori",
            slug="ikinci-favori",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            audience=self.student,
        )

        response = Client().get(
            "/cagrilar/favoriler/coz/",
            {"ids": f"{second_call.id},not-number,{hidden_call.id},{first_call.id},{second_call.id}"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([call["id"] for call in payload["calls"]], [second_call.id, first_call.id])
        self.assertEqual(payload["calls"][0]["url"], f"/cagrilar/{second_call.slug}-{second_call.id}/")

    def test_favorite_page_is_public_noindex_without_account_language(self) -> None:
        response = Client().get("/favoriler/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favoriler")
        self.assertContains(response, "bu cihazda saklanır")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)


def _structured_data(content: str) -> list[dict[str, Any]]:
    match = re.search(r'<script[^>]+type="application/ld\+json">(.*?)</script>', content)
    if not match:
        return []
    payload = json.loads(match.group(1))
    return payload if isinstance(payload, list) else [payload]
