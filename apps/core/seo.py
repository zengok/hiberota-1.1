from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape

from django.http import HttpRequest
from django.utils import timezone

from apps.blog.public import published_blog_posts
from apps.calls.detail import build_call_detail_path, published_call_queryset
from apps.calls.models import GrantCall
from apps.institutions.public import public_institutions

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


@dataclass(frozen=True)
class SitemapEntry:
    path: str
    lastmod: datetime | None = None


def build_robots_txt(request: HttpRequest) -> str:
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    return "\n".join(
        [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /health/",
            "Disallow: /favoriler/",
            "Disallow: /ebulten/onay/",
            "Disallow: /ebulten/yonet/",
            "Disallow: /ebulten/cikis/",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )


def sitemap_index_xml(request: HttpRequest) -> bytes:
    items = []
    for path in [
        "/sitemap-calls-open.xml",
        "/sitemap-calls-closed.xml",
        "/sitemap-institutions.xml",
        "/sitemap-blog.xml",
        "/sitemap-landing-pages.xml",
    ]:
        items.append(f"<sitemap><loc>{_xml_escape(request.build_absolute_uri(path))}</loc></sitemap>")
    return _xml_response("sitemapindex", items)


def sitemap_urlset_xml(request: HttpRequest, entries: Iterable[SitemapEntry]) -> bytes:
    items = []
    for entry in entries:
        item = f"<url><loc>{_xml_escape(request.build_absolute_uri(entry.path))}</loc>"
        if entry.lastmod:
            item += f"<lastmod>{timezone.localtime(entry.lastmod, UTC).date().isoformat()}</lastmod>"
        item += "</url>"
        items.append(item)
    return _xml_response("urlset", items)


def open_call_entries() -> Iterable[SitemapEntry]:
    calls = published_call_queryset().exclude(availability_status=GrantCall.AvailabilityStatus.CLOSED)
    for call in calls.order_by("-updated_at", "-first_seen_at"):
        yield SitemapEntry(path=build_call_detail_path(call), lastmod=call.updated_at)


def closed_call_entries() -> Iterable[SitemapEntry]:
    calls = published_call_queryset().filter(availability_status=GrantCall.AvailabilityStatus.CLOSED)
    for call in calls.order_by("-updated_at", "-first_seen_at"):
        yield SitemapEntry(path=build_call_detail_path(call), lastmod=call.updated_at)


def institution_entries() -> Iterable[SitemapEntry]:
    for institution in public_institutions().order_by("-updated_at", "name"):
        yield SitemapEntry(path=f"/kurumlar/{institution.slug}/", lastmod=institution.updated_at)


def blog_entries() -> Iterable[SitemapEntry]:
    for post in published_blog_posts().order_by("-updated_at", "-publish_at"):
        yield SitemapEntry(path=f"/proje-rehberi/{post.slug}/", lastmod=post.updated_at)


def landing_page_entries() -> Iterable[SitemapEntry]:
    for path in ["/", "/cagrilar/", "/kurumlar/", "/proje-rehberi/", "/hibe-anketi/", "/iletisim/"]:
        yield SitemapEntry(path=path)


def _xml_response(root_name: str, items: list[str]) -> bytes:
    body = "".join(items)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_name} xmlns="{SITEMAP_NS}">{body}</{root_name}>'.encode()


def _xml_escape(value: str) -> str:
    return escape(value, quote=True)
