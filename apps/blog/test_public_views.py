from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Any

import pytest
from django.test import Client, TestCase
from django.utils import timezone

from apps.blog.models import BlogAuthor, BlogPost


@pytest.mark.django_db
class BlogPublicViewTests(TestCase):
    def setUp(self) -> None:
        self.author = BlogAuthor.objects.create(name="HibeRota Editörü", slug="hiberota-editor", is_active=True)

    def _create_post(
        self,
        *,
        title: str,
        slug: str,
        status: str = BlogPost.Status.PUBLISHED,
        publish_offset_days: int = -1,
        body_html: str = "<p>Başvuru sürecini planlı ilerletin.</p>",
    ) -> BlogPost:
        return BlogPost.objects.create(
            title=title,
            slug=slug,
            excerpt=f"{title} kısa açıklaması",
            author=self.author,
            body_html=body_html,
            status=status,
            publish_at=timezone.now() + timedelta(days=publish_offset_days),
            reading_time_minutes=3,
            seo_title=f"{title} SEO",
            seo_description=f"{title} meta açıklaması",
        )

    def test_blog_list_shows_only_published_due_posts(self) -> None:
        published = self._create_post(title="Yayınlanan Rehber", slug="yayinlanan-rehber")
        self._create_post(title="Taslak Rehber", slug="taslak-rehber", status=BlogPost.Status.DRAFT)
        self._create_post(title="İleri Tarihli Rehber", slug="ileri-tarihli-rehber", publish_offset_days=2)

        response = Client().get("/proje-rehberi/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proje Rehberi")
        self.assertContains(response, published.title)
        self.assertContains(response, 'name="robots" content="index,follow"')
        self.assertContains(response, f"/proje-rehberi/{published.slug}/")
        self.assertNotIn("Taslak Rehber", content)
        self.assertNotIn("İleri Tarihli Rehber", content)
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_blog_detail_renders_published_post(self) -> None:
        post = self._create_post(
            title="Detaylı Rehber",
            slug="detayli-rehber",
            body_html="<h2>Hazırlık</h2><p><strong>Belgeleri</strong> kontrol edin.</p>",
        )

        response = Client().get(f"/proje-rehberi/{post.slug}/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detaylı Rehber")
        self.assertContains(response, "HibeRota Editörü")
        self.assertContains(response, "<h2>Hazırlık</h2>")
        self.assertContains(response, "Detaylı Rehber SEO")
        self.assertContains(response, f"/proje-rehberi/{post.slug}/")
        self.assertContains(response, 'property="og:type" content="article"')
        self.assertContains(response, 'property="og:title" content="Detaylı Rehber SEO"')
        self.assertContains(response, "Ana Sayfa")
        self.assertContains(response, "Proje Rehberi")
        structured_data = _structured_data(content)
        self.assertEqual([item["@type"] for item in structured_data], ["BreadcrumbList", "BlogPosting"])
        self.assertEqual(structured_data[1]["headline"], "Detaylı Rehber")
        self.assertEqual(structured_data[1]["author"]["name"], "HibeRota Editörü")
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_blog_detail_hides_unsafe_body_from_bypassed_db_write(self) -> None:
        post = self._create_post(
            title="Güvensiz Rehber",
            slug="guvensiz-rehber",
            body_html="<p>Metin</p><script>alert(1)</script>",
        )

        response = Client().get(f"/proje-rehberi/{post.slug}/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("<script>", content)


def _structured_data(content: str) -> list[dict[str, Any]]:
    match = re.search(r'<script[^>]+type="application/ld\+json">(.*?)</script>', content)
    if not match:
        return []
    payload = json.loads(match.group(1))
    return payload if isinstance(payload, list) else [payload]
