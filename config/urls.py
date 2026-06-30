"""Root URL configuration."""

from __future__ import annotations

from apps.calls.views import favorite_list
from apps.core.views import (
    home,
    robots_txt,
    rss_feed,
    security_policy,
    security_txt,
    sitemap_blog,
    sitemap_calls_closed,
    sitemap_calls_open,
    sitemap_index,
    sitemap_institutions,
    sitemap_landing_pages,
    veor_collection,
)
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", home, name="home"),
    path(".well-known/security.txt", security_txt, name="security-txt"),
    path("admin/", admin.site.urls),
    path("cagrilar/", include("apps.calls.urls")),
    path("favoriler/", favorite_list, name="favorite-list"),
    path("health/", include("apps.core.urls")),
    path("hibe-anketi/", include("apps.survey.urls")),
    path("iletisim/", include("apps.contact.urls")),
    path("kurumlar/", include("apps.institutions.urls")),
    path("ebulten/", include("apps.newsletter.urls")),
    path("proje-rehberi/", include("apps.blog.urls")),
    path("robots.txt", robots_txt, name="robots-txt"),
    path("rss/", rss_feed, name="rss-feed"),
    path("sitemap.xml", sitemap_index, name="sitemap-index"),
    path("sitemap-blog.xml", sitemap_blog, name="sitemap-blog"),
    path("sitemap-calls-closed.xml", sitemap_calls_closed, name="sitemap-calls-closed"),
    path("sitemap-calls-open.xml", sitemap_calls_open, name="sitemap-calls-open"),
    path("sitemap-institutions.xml", sitemap_institutions, name="sitemap-institutions"),
    path("sitemap-landing-pages.xml", sitemap_landing_pages, name="sitemap-landing-pages"),
    path("veor-collection/", veor_collection, name="veor-collection"),
    path("guvenlik/", security_policy, name="security-policy"),
]

handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"
