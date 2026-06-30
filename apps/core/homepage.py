from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Institution

HOME_CALL_LIMIT = 4
HOME_INSTITUTION_LIMIT = 6

QUICK_START_CARDS = [
    {"label": "Öğrenci", "href": "/ogrenciler-icin-hibeler/"},
    {"label": "Akademisyen", "href": "/akademisyenler-icin-fonlar/"},
    {"label": "Araştırmacı", "href": "/cagrilar/?hedef=arastirmaci"},
    {"label": "Girişimci", "href": "/cagrilar/?hedef=girisimci"},
    {"label": "KOBİ/Firma", "href": "/cagrilar/?hedef=kobi-firma"},
    {"label": "Kurumsal/Kamu/STK", "href": "/cagrilar/?hedef=kurumsal-kamu-stk"},
]


def _published_calls() -> QuerySet[GrantCall]:
    return (
        GrantCall.objects.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .select_related("institution")
        .prefetch_related("countries", "audiences")
    )


def get_homepage_context() -> dict[str, Any]:
    now = timezone.now()
    live_statuses = [
        GrantCall.AvailabilityStatus.OPEN,
        GrantCall.AvailabilityStatus.CLOSING_SOON,
        GrantCall.AvailabilityStatus.UPCOMING,
    ]
    base_calls = _published_calls().filter(availability_status__in=live_statuses)

    recent_turkey_calls = (
        base_calls.filter(countries__code="TR").order_by("-first_seen_at").distinct()[:HOME_CALL_LIMIT]
    )
    recent_world_calls = (
        base_calls.exclude(countries__code="TR").order_by("-first_seen_at").distinct()[:HOME_CALL_LIMIT]
    )
    upcoming_deadlines = (
        base_calls.filter(deadline_at__gte=now).order_by("deadline_at", "-first_seen_at").distinct()[:HOME_CALL_LIMIT]
    )
    featured_institutions = (
        Institution.objects.filter(is_active=True, is_verified=True)
        .select_related("country")
        .order_by("name")[:HOME_INSTITUTION_LIMIT]
    )

    return {
        "page_title": "HibeRota",
        "meta_description": (
            "Türkiye ve dünyadan hibe, fon ve proje çağrılarını resmi kaynak bağlantılarıyla takip edin."
        ),
        "canonical_path": "/",
        "robots": "index,follow",
        "quick_start_cards": QUICK_START_CARDS,
        "recent_turkey_calls": recent_turkey_calls,
        "recent_world_calls": recent_world_calls,
        "upcoming_deadlines": upcoming_deadlines,
        "featured_institutions": featured_institutions,
    }
