from __future__ import annotations

from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.blog.public import build_blog_detail_context, build_blog_list_context, published_blog_posts
from apps.core.structured_data import blog_posting_schema, breadcrumb_schema, structured_data_json


@require_GET
def blog_list(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/blog_list.html", build_blog_list_context(request.GET.get("sayfa")))


@require_GET
def blog_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(published_blog_posts(), slug=slug)
    try:
        context = build_blog_detail_context(post)
    except ValidationError as exc:
        raise Http404("Blog içeriği yayınlanabilir durumda değil.") from exc
    canonical_path = context["canonical_path"]
    context["structured_data_json"] = structured_data_json(
        [
            breadcrumb_schema(
                request,
                [
                    ("Ana Sayfa", "/"),
                    ("Proje Rehberi", "/proje-rehberi/"),
                    (post.title, canonical_path),
                ],
            ),
            blog_posting_schema(
                request,
                title=post.title,
                path=canonical_path,
                description=context["meta_description"],
                author_name=post.author.name,
                published_at=post.publish_at,
                modified_at=post.updated_at,
            ),
        ]
    )
    return render(request, "pages/blog_detail.html", context)
