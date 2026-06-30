from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator
from django.db.models import Count, Max, Q, QuerySet
from django.http import QueryDict

from apps.calls.models import GrantCall
from apps.institutions.models import Institution

INSTITUTIONS_PER_PAGE = 12
DETAIL_CALL_LIMIT = 8

LIVE_STATUSES = [
    GrantCall.AvailabilityStatus.UPCOMING,
    GrantCall.AvailabilityStatus.OPEN,
    GrantCall.AvailabilityStatus.CLOSING_SOON,
]


def public_institutions() -> QuerySet[Institution]:
    return (
        Institution.objects.filter(is_active=True, is_verified=True)
        .select_related("country")
        .annotate(
            open_call_count=Count(
                "grant_calls",
                filter=Q(
                    grant_calls__workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
                    grant_calls__availability_status__in=LIVE_STATUSES,
                ),
                distinct=True,
            ),
            published_call_count=Count(
                "grant_calls",
                filter=Q(grant_calls__workflow_status=GrantCall.WorkflowStatus.PUBLISHED),
                distinct=True,
            ),
            last_call_update=Max(
                "grant_calls__updated_at",
                filter=Q(grant_calls__workflow_status=GrantCall.WorkflowStatus.PUBLISHED),
            ),
        )
        .order_by("name")
    )


def build_institution_list_context(params: QueryDict) -> dict[str, Any]:
    institutions = public_institutions()
    query = params.get("q", "").strip()
    if query:
        institutions = institutions.filter(
            Q(name__icontains=query) | Q(short_name__icontains=query) | Q(country__name_tr__icontains=query)
        )

    paginator = Paginator(institutions, INSTITUTIONS_PER_PAGE)
    page = paginator.get_page(params.get("sayfa", "1"))

    return {
        "page_title": "Kurumlar | HibeRota",
        "meta_description": "Hibe ve fon çağrısı yayımlayan doğrulanmış kurumları ve aktif çağrı sayılarını inceleyin.",
        "canonical_path": "/kurumlar/",
        "robots": "noindex,follow" if query else "index,follow",
        "institutions_page": page,
        "result_count": institutions.count(),
        "query": query,
        "previous_page_url": _page_url(params, page.previous_page_number()) if page.has_previous() else "",
        "next_page_url": _page_url(params, page.next_page_number()) if page.has_next() else "",
    }


def build_institution_detail_context(institution: Institution) -> dict[str, Any]:
    published_calls = (
        GrantCall.objects.filter(institution=institution, workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .select_related("institution")
        .prefetch_related("countries", "audiences", "themes")
    )
    open_calls = published_calls.filter(availability_status__in=LIVE_STATUSES).order_by("-first_seen_at")[
        :DETAIL_CALL_LIMIT
    ]
    closed_calls = published_calls.filter(availability_status=GrantCall.AvailabilityStatus.CLOSED).order_by(
        "-first_seen_at"
    )[:DETAIL_CALL_LIMIT]

    return {
        "page_title": f"{institution} | HibeRota",
        "meta_description": _institution_description(institution),
        "canonical_path": f"/kurumlar/{institution.slug}/",
        "robots": "index,follow",
        "institution": institution,
        "open_calls": open_calls,
        "closed_calls": closed_calls,
        "country_distribution": country_distribution(institution),
        "theme_distribution": theme_distribution(institution),
        "last_data_update": published_calls.order_by("-updated_at").values_list("updated_at", flat=True).first(),
    }


def country_distribution(institution: Institution) -> list[dict[str, Any]]:
    return list(
        GrantCall.objects.filter(institution=institution, workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .values("countries__name_tr")
        .annotate(call_count=Count("id", distinct=True))
        .order_by("-call_count", "countries__name_tr")[:8]
    )


def theme_distribution(institution: Institution) -> list[dict[str, Any]]:
    return list(
        GrantCall.objects.filter(institution=institution, workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .values("themes__name_tr")
        .annotate(call_count=Count("id", distinct=True))
        .order_by("-call_count", "themes__name_tr")[:8]
    )


def _institution_description(institution: Institution) -> str:
    if institution.description:
        return institution.description[:155]
    return f"{institution} tarafından yayımlanan hibe ve fon çağrılarını HibeRota üzerinde inceleyin."


def _page_url(params: QueryDict, page_number: int) -> str:
    query = params.copy()
    query["sayfa"] = str(page_number)
    return f"/kurumlar/?{query.urlencode()}"
