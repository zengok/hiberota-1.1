from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.utils import timezone

from apps.blog.models import BlogPost, validate_rich_text_allowlist
from apps.calls.models import GrantCall


def published_blog_posts() -> QuerySet[BlogPost]:
    return (
        BlogPost.objects.select_related("author")
        .filter(
            status=BlogPost.Status.PUBLISHED,
            publish_at__lte=timezone.now(),
            author__is_active=True,
        )
        .order_by("-publish_at", "-created_at")
    )


def build_blog_list_context(page_number: str | None = None) -> dict[str, Any]:
    paginator = Paginator(published_blog_posts(), 12)
    posts_page = paginator.get_page(page_number)
    return {
        "page_title": "Proje Rehberi | HibeRota",
        "meta_description": "Hibe, fon ve proje başvuruları için rehber içerikler.",
        "canonical_path": "/proje-rehberi/",
        "robots": "index,follow",
        "posts_page": posts_page,
    }


def build_blog_detail_context(post: BlogPost) -> dict[str, Any]:
    validate_rich_text_allowlist(post.body_html)
    return {
        "page_title": post.seo_title or f"{post.title} | HibeRota",
        "meta_description": post.seo_description or post.excerpt,
        "canonical_path": f"/proje-rehberi/{post.slug}/",
        "robots": "index,follow",
        "og_type": "article",
        "post": post,
        "related_calls": post.related_calls.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED),
    }
