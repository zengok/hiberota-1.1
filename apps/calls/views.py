from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from apps.calls.detail import build_call_detail_context, build_call_detail_path, published_call_queryset
from apps.calls.embed import build_call_embed_path, embed_csp_header, is_embed_rate_limited
from apps.calls.favorites import resolve_favorite_calls
from apps.calls.filters import build_page_url, get_call_list_context
from apps.calls.models import GrantCall
from apps.core.structured_data import breadcrumb_schema, structured_data_json
from apps.core.views import gone


@require_GET
def call_list(request: HttpRequest) -> HttpResponse:
    context = get_call_list_context(request.GET)
    calls_page = context["calls_page"]
    context["previous_page_url"] = (
        build_page_url(request.GET, calls_page.previous_page_number()) if calls_page.has_previous() else ""
    )
    context["next_page_url"] = (
        build_page_url(request.GET, calls_page.next_page_number()) if calls_page.has_next() else ""
    )
    return render(request, "pages/call_list.html", context)


@require_GET
def call_detail(request: HttpRequest, slug: str, pk: int) -> HttpResponse:
    archived_call = GrantCall.objects.filter(pk=pk, workflow_status=GrantCall.WorkflowStatus.ARCHIVED).exists()
    if archived_call:
        return gone(request)

    call = get_object_or_404(published_call_queryset(), pk=pk)
    canonical_path = build_call_detail_path(call)
    if slug != call.slug:
        return redirect(canonical_path, permanent=True)
    context = build_call_detail_context(call)
    context["structured_data_json"] = structured_data_json(
        [
            breadcrumb_schema(
                request,
                [
                    ("Ana Sayfa", "/"),
                    ("Çağrılar", "/cagrilar/"),
                    (call.title, canonical_path),
                ],
            )
        ]
    )
    return render(request, "pages/call_detail.html", context)


@require_GET
@xframe_options_exempt
def call_embed(request: HttpRequest, slug: str, pk: int) -> HttpResponse:
    archived_call = GrantCall.objects.filter(pk=pk, workflow_status=GrantCall.WorkflowStatus.ARCHIVED).exists()
    if archived_call:
        return gone(request)

    call = get_object_or_404(published_call_queryset(), pk=pk)
    canonical_path = build_call_embed_path(call)
    if slug != call.slug:
        return redirect(canonical_path, permanent=True)
    if is_embed_rate_limited(request, call.id):
        return HttpResponse("Too many requests", content_type="text/plain; charset=utf-8", status=429)

    response = render(
        request,
        "embeds/call_badge.html",
        {
            "call": call,
            "canonical_path": build_call_detail_path(call),
            "robots": "noindex,follow",
        },
    )
    response["Content-Security-Policy"] = embed_csp_header()
    response["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response["Cache-Control"] = "public, max-age=300"
    return response


@require_GET
def favorite_resolve(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"calls": resolve_favorite_calls(request.GET.get("ids", ""))})


@require_GET
def favorite_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/favorites.html",
        {
            "page_title": "Favoriler | HibeRota",
            "meta_description": "Bu cihazda kaydettiğiniz hibe ve fon çağrılarını görüntüleyin.",
            "canonical_path": "/favoriler/",
            "robots": "noindex,follow",
        },
    )
