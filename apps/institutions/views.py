from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.core.structured_data import breadcrumb_schema, institution_schema, structured_data_json
from apps.institutions.public import (
    build_institution_detail_context,
    build_institution_list_context,
    public_institutions,
)


@require_GET
def institution_list(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/institution_list.html", build_institution_list_context(request.GET))


@require_GET
def institution_detail(request: HttpRequest, slug: str) -> HttpResponse:
    institution = get_object_or_404(public_institutions(), slug=slug)
    context = build_institution_detail_context(institution)
    canonical_path = context["canonical_path"]
    context["structured_data_json"] = structured_data_json(
        [
            breadcrumb_schema(
                request,
                [
                    ("Ana Sayfa", "/"),
                    ("Kurumlar", "/kurumlar/"),
                    (str(institution), canonical_path),
                ],
            ),
            institution_schema(
                request,
                name=str(institution),
                path=canonical_path,
                country=institution.country.name_tr,
                website_url=institution.website_url,
            ),
        ]
    )
    return render(request, "pages/institution_detail.html", context)
