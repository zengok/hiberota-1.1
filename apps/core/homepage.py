from __future__ import annotations

from typing import Any

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution

HOME_CALL_LIMIT = 4
HOME_INSTITUTION_LIMIT = 6

QUICK_START_CARDS = [
    {
        "label": "Öğrenci",
        "description": "Burs, araştırma ve gençlik destekleri",
        "href": "/cagrilar/?hedef=student&hedef=graduate_student",
        "icon": "student",
    },
    {
        "label": "Akademisyen",
        "description": "Üniversite ve bilimsel proje fonları",
        "href": "/cagrilar/?hedef=academic",
        "icon": "academic",
    },
    {
        "label": "Araştırmacı",
        "description": "Ar-Ge ve araştırma odaklı çağrılar",
        "href": "/cagrilar/?hedef=researcher",
        "icon": "researcher",
    },
    {
        "label": "Girişimci",
        "description": "Girişim ve startup destekleri",
        "href": "/cagrilar/?hedef=entrepreneur&hedef=startup",
        "icon": "entrepreneur",
    },
    {
        "label": "KOBİ/Firma",
        "description": "KOBİ ve şirketlere yönelik destekler",
        "href": "/cagrilar/?hedef=sme&hedef=company",
        "icon": "company",
    },
    {
        "label": "Kurumsal/Kamu/STK",
        "description": "Kamu, belediye, STK ve konsorsiyum çağrıları",
        "href": "/cagrilar/?hedef=ngo&hedef=municipality&hedef=public_institution&hedef=consortium",
        "icon": "institution",
    },
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
    hero_call = (
        base_calls.filter(deadline_at__gte=now)
        .order_by("-is_featured", "deadline_at", "-first_seen_at")
        .distinct()
        .first()
        or base_calls.order_by("-is_featured", "-first_seen_at").distinct().first()
    )
    featured_institutions = (
        Institution.objects.filter(is_active=True, is_verified=True)
        .select_related("country")
        .annotate(
            open_call_count=Count(
                "grant_calls",
                filter=Q(
                    grant_calls__workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
                    grant_calls__availability_status__in=live_statuses,
                ),
                distinct=True,
            )
        )
        .order_by("name")[:HOME_INSTITUTION_LIMIT]
    )
    verified_institutions = Institution.objects.filter(is_active=True, is_verified=True)
    verified_institution_country_ids = verified_institutions.values("country_id").distinct()

    return {
        "page_title": "HibeRota",
        "meta_description": (
            "Türkiye ve dünyadan hibe, fon ve proje çağrılarını resmi kaynak bağlantılarıyla takip edin."
        ),
        "canonical_path": "/",
        "robots": "index,follow",
        "quick_start_cards": QUICK_START_CARDS,
        "hero_call": hero_call,
        "recent_turkey_calls": recent_turkey_calls,
        "recent_world_calls": recent_world_calls,
        "upcoming_deadlines": upcoming_deadlines,
        "featured_institutions": featured_institutions,
        "total_calls_count": _format_count(base_calls.distinct().count()),
        "total_institutions_count": _format_count(verified_institutions.count()),
        "total_countries_count": _format_count(
            Country.objects.filter(is_active=True, id__in=verified_institution_country_ids).count()
        ),
    }


def _format_count(value: int) -> str:
    return f"{value:,}".replace(",", ".")
