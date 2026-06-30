from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.core.feeds import latest_calls_rss
from apps.core.homepage import get_homepage_context
from apps.core.seo import (
    blog_entries,
    build_robots_txt,
    closed_call_entries,
    institution_entries,
    landing_page_entries,
    open_call_entries,
    sitemap_index_xml,
    sitemap_urlset_xml,
)
from apps.core.structured_data import organization_schema, structured_data_json, website_schema


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    context = get_homepage_context()
    context["structured_data_json"] = structured_data_json([website_schema(request), organization_schema(request)])
    return render(request, "pages/home.html", context)


@require_GET
def veor_collection(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/veor_collection.html",
        {
            "page_title": "Veor Collection | HibeRota",
            "meta_description": (
                "HibeRota'nın Veor Collection tarafından geliştirilen bir dijital ürün olduğunu açıklar."
            ),
            "robots": "noindex,follow",
            "canonical_path": "/veor-collection/",
        },
    )


@require_GET
def security_policy(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/security_policy.html",
        {
            "page_title": "Güvenlik Bildirimi | HibeRota",
            "meta_description": "HibeRota sorumlu güvenlik bildirimi kapsamı ve iletişim yöntemi.",
            "robots": "index,follow",
            "canonical_path": "/guvenlik/",
            "security_contact": settings.SECURITY_TXT_CONTACT,
        },
    )


@require_GET
def security_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        f"Contact: {settings.SECURITY_TXT_CONTACT}",
        f"Policy: {request.build_absolute_uri('/guvenlik/')}",
        "Preferred-Languages: tr, en",
        "Canonical: " + request.build_absolute_uri("/.well-known/security.txt"),
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


@require_GET
def robots_txt(request: HttpRequest) -> HttpResponse:
    return HttpResponse(build_robots_txt(request), content_type="text/plain; charset=utf-8")


@require_GET
def sitemap_index(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_index_xml(request), content_type="application/xml")


@require_GET
def sitemap_calls_open(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_urlset_xml(request, open_call_entries()), content_type="application/xml")


@require_GET
def sitemap_calls_closed(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_urlset_xml(request, closed_call_entries()), content_type="application/xml")


@require_GET
def sitemap_institutions(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_urlset_xml(request, institution_entries()), content_type="application/xml")


@require_GET
def sitemap_blog(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_urlset_xml(request, blog_entries()), content_type="application/xml")


@require_GET
def sitemap_landing_pages(request: HttpRequest) -> HttpResponse:
    return HttpResponse(sitemap_urlset_xml(request, landing_page_entries()), content_type="application/xml")


@require_GET
def rss_feed(request: HttpRequest) -> HttpResponse:
    return HttpResponse(latest_calls_rss(request), content_type="application/rss+xml")


def error_response(request: HttpRequest, *, status_code: int, title: str, message: str) -> HttpResponse:
    return render(
        request,
        "errors/status.html",
        {
            "status_code": status_code,
            "error_title": title,
            "error_message": message,
            "page_title": f"{status_code} | HibeRota",
            "meta_description": message,
            "robots": "noindex,follow",
        },
        status=status_code,
    )


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return error_response(
        request,
        status_code=404,
        title="Sayfa bulunamadı",
        message="Aradığınız sayfa taşınmış, silinmiş veya hiç yayınlanmamış olabilir.",
    )


def gone(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return error_response(
        request,
        status_code=410,
        title="Bu kayıt yayından kaldırıldı",
        message="Bu içerik artık HibeRota üzerinde aktif olarak yayınlanmıyor.",
    )


def too_many_requests(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return error_response(
        request,
        status_code=429,
        title="Çok fazla istek gönderildi",
        message="Kısa süre içinde çok fazla deneme yapıldı. Lütfen biraz bekleyip yeniden deneyin.",
    )


def server_error(request: HttpRequest) -> HttpResponse:
    return error_response(
        request,
        status_code=500,
        title="Beklenmeyen bir hata oluştu",
        message="Sistem isteğinizi şu anda tamamlayamıyor. Lütfen daha sonra yeniden deneyin.",
    )


@require_GET
def live(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "hiberota"})


@require_GET
def ready(request: HttpRequest) -> JsonResponse:
    checks = {"database": False, "cache": False}

    try:
        connections["default"].cursor().execute("SELECT 1")
        checks["database"] = True
    except OperationalError:
        checks["database"] = False

    try:
        cache.set("healthcheck", "ok", timeout=5)
        checks["cache"] = cache.get("healthcheck") == "ok"
    except Exception:
        checks["cache"] = False

    status_code = 200 if all(checks.values()) else 503
    return JsonResponse({"status": "ok" if status_code == 200 else "unavailable", "checks": checks}, status=status_code)
