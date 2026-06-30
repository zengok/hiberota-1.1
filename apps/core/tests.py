from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Any

import pytest
from defusedxml import ElementTree
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from apps.blog.models import BlogAuthor, BlogPost
from apps.calls.models import GrantCall
from apps.core.views import server_error, too_many_requests
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@pytest.mark.django_db
class HealthEndpointTests(TestCase):
    def test_live_health_endpoint(self) -> None:
        response = Client().get("/health/live")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_ready_health_endpoint(self) -> None:
        response = Client().get("/health/ready")

        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json()["checks"]["database"], True)


class PublicLayoutTests(TestCase):
    def test_homepage_uses_public_layout(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>HibeRota</title>")
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertContains(response, 'property="og:type" content="website"')
        self.assertContains(response, 'property="og:title" content="HibeRota"')
        self.assertContains(response, 'name="twitter:card" content="summary"')
        self.assertContains(response, "/static/js/share.js")
        self.assertContains(response, 'aria-label="Ana navigasyon"')
        self.assertContains(response, "Çağrılar")
        self.assertContains(response, "Kurumlar")
        self.assertNotIn("google-site-verification", content)
        self.assertNotIn("msvalidate.01", content)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    @override_settings(GOOGLE_SITE_VERIFICATION="google-token", BING_SITE_VERIFICATION="bing-token")
    def test_homepage_renders_search_engine_verification_meta_from_environment(self) -> None:
        response = Client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="google-site-verification" content="google-token"')
        self.assertContains(response, 'name="msvalidate.01" content="bing-token"')

    def test_homepage_exposes_website_and_organization_structured_data(self) -> None:
        response = Client(HTTP_HOST="testserver").get("/")
        structured_data = _structured_data(response.content.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["@type"] for item in structured_data], ["WebSite", "Organization"])
        self.assertEqual(structured_data[0]["url"], "http://testserver/")

    def test_homepage_does_not_render_ga4_controls_without_measurement_id(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("googletagmanager.com/gtag/js", content)
        self.assertNotIn("data-analytics-consent", content)
        self.assertNotIn("/static/js/analytics_consent.js", content)

    @override_settings(GA4_MEASUREMENT_ID="G-2HHZH6D0QT")
    def test_homepage_renders_consent_controls_without_loading_ga4_script(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.gtag("consent", "default"')
        self.assertContains(response, 'data-analytics-consent data-ga4-measurement-id="G-2HHZH6D0QT"')
        self.assertContains(response, "/static/js/analytics_consent.js")
        self.assertContains(response, 'data-cmp-enabled="false"')
        self.assertContains(response, 'data-adsense-client-id=""')
        self.assertNotIn("googletagmanager.com/gtag/js", content)
        self.assertNotIn("pagead2.googlesyndication.com", content)

    @override_settings(
        GA4_MEASUREMENT_ID="G-2HHZH6D0QT",
        ADSENSE_ENABLED=True,
        ADSENSE_CLIENT_ID="ca-pub-1234567890123456",
    )
    def test_homepage_passes_adsense_client_to_consent_loader_when_ready(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-adsense-client-id="ca-pub-1234567890123456"')
        self.assertNotIn("pagead2.googlesyndication.com", content)

    @override_settings(
        GA4_MEASUREMENT_ID="G-2HHZH6D0QT",
        CMP_ENABLED=True,
        CMP_PROVIDER_NAME="Example Certified CMP",
        CMP_SCRIPT_URL="https://cmp.example.test/cmp.js",
    )
    def test_homepage_renders_cmp_script_without_local_banner(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'window.gtag("consent", "default"')
        self.assertContains(response, 'src="https://cmp.example.test/cmp.js"')
        self.assertContains(response, 'data-cmp-provider="Example Certified CMP"')
        self.assertContains(response, 'data-cmp-enabled="true"')
        self.assertNotIn("data-analytics-consent", content)
        self.assertNotIn("googletagmanager.com/gtag/js", content)

    @override_settings(
        GA4_MEASUREMENT_ID="G-2HHZH6D0QT",
        CMP_ENABLED=True,
        CMP_PROVIDER_NAME="Invalid CMP",
        CMP_SCRIPT_URL="http://cmp.example.test/cmp.js",
    )
    def test_homepage_ignores_non_https_cmp_script_url(self) -> None:
        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("http://cmp.example.test/cmp.js", content)
        self.assertContains(response, 'data-analytics-consent data-ga4-measurement-id="G-2HHZH6D0QT"')

    def test_veor_collection_brand_page_uses_public_layout(self) -> None:
        response = Client().get("/veor-collection/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Veor Collection | HibeRota</title>")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, "HibeRota, Veor Collection tarafından geliştirilen bir dijital üründür.")
        self.assertContains(response, 'href="https://veorcollection.com"')
        self.assertContains(response, 'rel="noopener noreferrer"')
        self.assertContains(response, 'target="_blank"')
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_footer_links_to_veor_collection_brand_page(self) -> None:
        response = Client().get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/veor-collection/"')
        self.assertContains(response, "Veor Collection")

    @override_settings(SECURITY_TXT_CONTACT="mailto:security@example.invalid")
    def test_public_security_policy_page_uses_safe_public_content(self) -> None:
        response = Client().get("/guvenlik/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Güvenlik Bildirimi | HibeRota</title>")
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertContains(response, "mailto:security@example.invalid")
        self.assertContains(response, "DDoS")
        self.assertContains(response, "sosyal mühendislik")
        self.assertContains(response, "kalıcılık")
        self.assertNotIn("firewall", content.lower())
        self.assertNotIn("secret", content.lower())
        self.assertNotIn("admin path", content.lower())

    @override_settings(SECURITY_TXT_CONTACT="mailto:security@example.invalid")
    def test_security_txt_uses_environment_contact_and_policy_url(self) -> None:
        response = Client(HTTP_HOST="testserver").get("/.well-known/security.txt")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("Contact: mailto:security@example.invalid", content)
        self.assertIn("Policy: http://testserver/guvenlik/", content)
        self.assertIn("Preferred-Languages: tr, en", content)
        self.assertIn("Canonical: http://testserver/.well-known/security.txt", content)


class SecurityHeaderTests(TestCase):
    def test_public_pages_receive_csp_and_baseline_security_headers(self) -> None:
        response = Client().get("/")
        content = response.content.decode()
        csp = response["Content-Security-Policy"]
        nonce_match = re.search(r"script-src .*'nonce-([^']+)'", csp)

        self.assertIsNotNone(nonce_match)
        if nonce_match is None:
            self.fail("CSP script nonce is missing")
        self.assertIn(f'nonce="{nonce_match.group(1)}"', content)
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("https://cdn.jsdelivr.net", csp)
        self.assertIn("https://www.googletagmanager.com", csp)
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertIn("geolocation=()", response["Permissions-Policy"])
        self.assertEqual(response["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertEqual(response["Cross-Origin-Resource-Policy"], "same-origin")
        self.assertEqual(response["X-Permitted-Cross-Domain-Policies"], "none")

    @override_settings(CMP_SCRIPT_URL="https://cmp.example.test/cmp.js")
    def test_csp_allows_configured_https_cmp_origin(self) -> None:
        response = Client().get("/")

        self.assertIn("https://cmp.example.test", response["Content-Security-Policy"])

    @override_settings(CMP_SCRIPT_URL="http://cmp.example.test/cmp.js")
    def test_csp_rejects_non_https_cmp_origin(self) -> None:
        response = Client().get("/")

        self.assertNotIn("http://cmp.example.test", response["Content-Security-Policy"])

    @override_settings(
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=False,
    )
    def test_hsts_header_is_available_for_secure_production_like_requests(self) -> None:
        response = Client().get("/", secure=True)

        self.assertEqual(response["Strict-Transport-Security"], "max-age=31536000; includeSubDomains")


@pytest.mark.django_db
class SeoEndpointTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.audience = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.institution = Institution.objects.create(
            country=self.country,
            name="SEO Kurumu",
            slug="seo-kurumu",
            is_verified=True,
        )
        self.source = Source.objects.create(
            institution=self.institution,
            name="SEO Kaynağı",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="seo-kaynagi",
        )
        self.open_call = self._create_call(
            title="Açık SEO Çağrısı",
            slug="acik-seo-cagrisi",
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )
        self.closed_call = self._create_call(
            title="Kapalı SEO Çağrısı",
            slug="kapali-seo-cagrisi",
            availability_status=GrantCall.AvailabilityStatus.CLOSED,
        )
        author = BlogAuthor.objects.create(name="SEO Yazarı", slug="seo-yazari", is_active=True)
        BlogPost.objects.create(
            title="SEO Rehberi",
            slug="seo-rehberi",
            excerpt="SEO rehberi kısa açıklaması.",
            author=author,
            body_html="<p>Yayınlanmış rehber.</p>",
            status=BlogPost.Status.PUBLISHED,
            publish_at=timezone.now(),
        )

    def test_robots_txt_exposes_sitemap_and_blocks_internal_paths(self) -> None:
        response = Client(HTTP_HOST="testserver").get("/robots.txt")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("User-agent: *", content)
        self.assertIn("Disallow: /admin/", content)
        self.assertIn("Disallow: /health/", content)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", content)

    def test_sitemap_index_lists_expected_sitemaps(self) -> None:
        response = Client(HTTP_HOST="testserver").get("/sitemap.xml")
        root = ElementTree.fromstring(response.content)
        locations = [item.text for item in root.findall("sm:sitemap/sm:loc", SITEMAP_NS)]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertEqual(
            locations,
            [
                "http://testserver/sitemap-calls-open.xml",
                "http://testserver/sitemap-calls-closed.xml",
                "http://testserver/sitemap-institutions.xml",
                "http://testserver/sitemap-blog.xml",
                "http://testserver/sitemap-landing-pages.xml",
            ],
        )

    def test_call_sitemaps_split_open_and_closed_calls(self) -> None:
        open_response = Client(HTTP_HOST="testserver").get("/sitemap-calls-open.xml")
        closed_response = Client(HTTP_HOST="testserver").get("/sitemap-calls-closed.xml")

        open_locations = self._sitemap_locations(open_response.content)
        closed_locations = self._sitemap_locations(closed_response.content)

        self.assertIn(f"http://testserver/cagrilar/acik-seo-cagrisi-{self.open_call.id}/", open_locations)
        self.assertNotIn(f"http://testserver/cagrilar/kapali-seo-cagrisi-{self.closed_call.id}/", open_locations)
        self.assertIn(f"http://testserver/cagrilar/kapali-seo-cagrisi-{self.closed_call.id}/", closed_locations)
        self.assertNotIn(f"http://testserver/cagrilar/acik-seo-cagrisi-{self.open_call.id}/", closed_locations)

    def test_supporting_sitemaps_include_public_indexable_pages(self) -> None:
        institution_response = Client(HTTP_HOST="testserver").get("/sitemap-institutions.xml")
        blog_response = Client(HTTP_HOST="testserver").get("/sitemap-blog.xml")
        landing_response = Client(HTTP_HOST="testserver").get("/sitemap-landing-pages.xml")

        self.assertIn("http://testserver/kurumlar/seo-kurumu/", self._sitemap_locations(institution_response.content))
        self.assertIn("http://testserver/proje-rehberi/seo-rehberi/", self._sitemap_locations(blog_response.content))
        self.assertEqual(
            self._sitemap_locations(landing_response.content),
            [
                "http://testserver/",
                "http://testserver/cagrilar/",
                "http://testserver/kurumlar/",
                "http://testserver/proje-rehberi/",
                "http://testserver/hibe-anketi/",
                "http://testserver/iletisim/",
            ],
        )

    def test_rss_feed_lists_latest_published_calls(self) -> None:
        hidden_call = self._create_call(
            title="Gizli RSS Çağrısı",
            slug="gizli-rss-cagrisi",
            availability_status=GrantCall.AvailabilityStatus.OPEN,
        )
        hidden_call.workflow_status = GrantCall.WorkflowStatus.REVIEW
        hidden_call.save()

        response = Client(HTTP_HOST="testserver").get("/rss/")
        root = ElementTree.fromstring(response.content)
        item_titles = [item.findtext("title") for item in root.findall("channel/item")]
        item_links = [item.findtext("link") for item in root.findall("channel/item")]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/rss+xml")
        self.assertEqual(root.tag, "rss")
        self.assertEqual(root.attrib["version"], "2.0")
        self.assertIn("Açık SEO Çağrısı", item_titles)
        self.assertIn("Kapalı SEO Çağrısı", item_titles)
        self.assertNotIn("Gizli RSS Çağrısı", item_titles)
        self.assertIn(f"http://testserver/cagrilar/acik-seo-cagrisi-{self.open_call.id}/", item_links)

    def _create_call(self, *, title: str, slug: str, availability_status: str) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=self.source,
            institution=self.institution,
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"seo-fingerprint-{slug}",
            first_seen_at=now,
            application_open_at=now,
            deadline_at=now + timedelta(days=10),
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=availability_status,
            published_at=now,
        )
        call.countries.add(self.country)
        call.audiences.add(self.audience)
        return call

    def _sitemap_locations(self, content: bytes) -> list[str]:
        root = ElementTree.fromstring(content)
        return [item.text or "" for item in root.findall("sm:url/sm:loc", SITEMAP_NS)]


def _structured_data(content: str) -> list[dict[str, Any]]:
    match = re.search(r'<script[^>]+type="application/ld\+json">(.*?)</script>', content)
    if not match:
        return []
    payload = json.loads(match.group(1))
    return payload if isinstance(payload, list) else [payload]


class PublicErrorPageTests(TestCase):
    def test_404_page_uses_public_noindex_layout(self) -> None:
        response = Client().get("/olmayan-sayfa/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Sayfa bulunamadı", status_code=404)
        self.assertContains(response, 'name="robots" content="noindex,follow"', status_code=404)
        self.assertContains(response, "Ana sayfaya dön", status_code=404)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_429_page_uses_public_noindex_layout(self) -> None:
        request = RequestFactory().get("/cagrilar/")

        response = too_many_requests(request)
        content = response.content.decode()

        self.assertEqual(response.status_code, 429)
        self.assertIn("Çok fazla istek gönderildi", content)
        self.assertIn('name="robots" content="noindex,follow"', content)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_500_page_uses_public_noindex_layout(self) -> None:
        request = RequestFactory().get("/cagrilar/")

        response = server_error(request)
        content = response.content.decode()

        self.assertEqual(response.status_code, 500)
        self.assertIn("Beklenmeyen bir hata oluştu", content)
        self.assertIn('name="robots" content="noindex,follow"', content)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)


@pytest.mark.django_db
class HomepageTests(TestCase):
    def setUp(self) -> None:
        self.turkey = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.germany = Country.objects.create(code="DE", name_tr="Almanya", name_en="Germany", is_europe=True)
        self.audience = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.institution = Institution.objects.create(
            country=self.turkey,
            name="Türkiye Kurumu",
            slug="turkiye-kurumu",
            is_verified=True,
        )
        self.world_institution = Institution.objects.create(
            country=self.germany,
            name="Dünya Kurumu",
            slug="dunya-kurumu",
            is_verified=True,
        )
        self.source = Source.objects.create(
            institution=self.institution,
            name="Türkiye Kaynağı",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="turkiye-kaynagi",
        )
        self.world_source = Source.objects.create(
            institution=self.world_institution,
            name="Dünya Kaynağı",
            base_url="https://world.example.org",
            listing_url="https://world.example.org/calls",
            source_type=Source.SourceType.FEED,
            adapter_key="dunya-kaynagi",
        )

    def _create_call(
        self,
        *,
        title: str,
        slug: str,
        source: Source,
        institution: Institution,
        country: Country,
        workflow_status: str = GrantCall.WorkflowStatus.PUBLISHED,
    ) -> GrantCall:
        now = timezone.now()
        call = GrantCall.objects.create(
            title=title,
            slug=slug,
            source=source,
            institution=institution,
            official_url=f"https://example.org/{slug}",
            canonical_source_url=f"https://example.org/{slug}/canonical",
            fingerprint=f"fingerprint-{slug}",
            first_seen_at=now,
            application_open_at=now,
            deadline_at=now + timedelta(days=10),
            workflow_status=workflow_status,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            published_at=now,
        )
        call.countries.add(country)
        call.audiences.add(self.audience)
        return call

    def test_homepage_lists_published_calls_and_featured_institutions(self) -> None:
        self._create_call(
            title="Türkiye Hibe Çağrısı",
            slug="turkiye-hibe-cagrisi",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
        )
        self._create_call(
            title="Dünya Fon Çağrısı",
            slug="dunya-fon-cagrisi",
            source=self.world_source,
            institution=self.world_institution,
            country=self.germany,
        )
        self._create_call(
            title="Taslak Çağrı",
            slug="taslak-cagri",
            source=self.source,
            institution=self.institution,
            country=self.turkey,
            workflow_status=GrantCall.WorkflowStatus.REVIEW,
        )

        response = Client().get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hızlı başlangıç")
        self.assertContains(response, "Son Türkiye çağrıları")
        self.assertContains(response, "Türkiye Hibe Çağrısı")
        self.assertContains(response, "Son dünya çağrıları")
        self.assertContains(response, "Dünya Fon Çağrısı")
        self.assertContains(response, "Yaklaşan son tarihler")
        self.assertContains(response, "Türkiye Kurumu")
        self.assertIn(">2</strong> aktif çağrı", content)
        self.assertIn(">2</strong> kurum", content)
        self.assertIn(">2</strong> ülke", content)
        self.assertContains(response, "Türkiye · 1 açık çağrı")
        self.assertNotIn("Taslak Çağrı", content)
        self.assertNotIn("1.240 aktif çağrı", content)
        self.assertContains(response, "data-favorites-panel")
        self.assertContains(response, "hidden")
