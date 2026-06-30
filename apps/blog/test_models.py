from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.blog.models import BlogAuthor, BlogPost


@pytest.mark.django_db
class TestBlogModel:
    def test_blog_post_accepts_allowlisted_rich_text(self) -> None:
        author = BlogAuthor.objects.create(name="Editör", slug="editor")
        post = BlogPost(
            title="Proje Rehberi",
            slug="proje-rehberi",
            excerpt="Kısa açıklama",
            author=author,
            body_html='<h2>Başlık</h2><p><strong>Metin</strong> ve <a href="https://example.org">link</a>.</p>',
            status=BlogPost.Status.PUBLISHED,
            publish_at=timezone.now(),
        )

        post.full_clean()

    def test_blog_post_rejects_unsafe_rich_text(self) -> None:
        author = BlogAuthor.objects.create(name="Editör", slug="editor")
        post = BlogPost(
            title="Güvensiz İçerik",
            slug="guvensiz-icerik",
            excerpt="Kısa açıklama",
            author=author,
            body_html='<p onclick="alert(1)">Metin</p><script>alert(1)</script>',
        )

        with pytest.raises(ValidationError):
            post.full_clean()

    def test_scheduled_post_requires_future_publish_date(self) -> None:
        author = BlogAuthor.objects.create(name="Editör", slug="editor")
        post = BlogPost(
            title="Planlı İçerik",
            slug="planli-icerik",
            excerpt="Kısa açıklama",
            author=author,
            body_html="<p>Metin</p>",
            status=BlogPost.Status.SCHEDULED,
            publish_at=timezone.now() - timedelta(minutes=1),
        )

        with pytest.raises(ValidationError):
            post.full_clean()
