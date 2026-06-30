from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db.models import Q, QuerySet

from apps.calls.detail import build_call_detail_path
from apps.calls.models import GrantCall
from apps.institutions.models import Country
from apps.taxonomy.models import AudienceType, OrganizationSize, ProgramType, Region, Sector, Theme

MATCH_LIMIT = 8
DEFAULT_STATUSES = [
    GrantCall.AvailabilityStatus.OPEN,
    GrantCall.AvailabilityStatus.CLOSING_SOON,
    GrantCall.AvailabilityStatus.UPCOMING,
]


@dataclass(frozen=True)
class SurveyProfile:
    query: str
    audience: AudienceType
    organization_size: OrganizationSize | None = None
    country: Country | None = None
    region: Region | None = None
    sector: Sector | None = None
    theme: Theme | None = None
    program_type: ProgramType | None = None
    availability_status: str = ""


@dataclass(frozen=True)
class MatchedCall:
    call: GrantCall
    score: int
    reasons: list[str]
    url: str


def profile_from_cleaned_data(cleaned_data: dict[str, Any]) -> SurveyProfile:
    return SurveyProfile(
        query=cleaned_data.get("q", "").strip(),
        audience=cleaned_data["audience"],
        organization_size=cleaned_data.get("organization_size"),
        country=cleaned_data.get("country"),
        region=cleaned_data.get("region"),
        sector=cleaned_data.get("sector"),
        theme=cleaned_data.get("theme"),
        program_type=cleaned_data.get("program_type"),
        availability_status=cleaned_data.get("availability_status", ""),
    )


def match_calls(profile: SurveyProfile, limit: int = MATCH_LIMIT) -> list[MatchedCall]:
    calls = _eligible_calls(profile)
    matches = sorted((_score_call(call, profile) for call in calls[:100]), key=lambda item: item.score, reverse=True)
    return [match for match in matches if match.score > 0][:limit]


def _eligible_calls(profile: SurveyProfile) -> QuerySet[GrantCall]:
    calls = (
        GrantCall.objects.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .filter(audiences=profile.audience)
        .select_related("institution")
        .prefetch_related("countries", "audiences", "sectors", "themes", "program_types", "organization_sizes")
        .distinct()
    )

    if profile.availability_status:
        calls = calls.filter(availability_status=profile.availability_status)
    else:
        calls = calls.filter(availability_status__in=DEFAULT_STATUSES)

    if profile.country is not None:
        calls = calls.filter(countries=profile.country)
    if profile.region is not None:
        calls = calls.filter(Q(regions=profile.region) | Q(countries__region_code=profile.region.key))
    if profile.organization_size is not None:
        calls = calls.filter(organization_sizes=profile.organization_size)

    return calls.order_by("-first_seen_at")


def _score_call(call: GrantCall, profile: SurveyProfile) -> MatchedCall:
    score = 40
    reasons = [f"Hedef kitle uyumlu: {profile.audience.name_tr}"]

    if profile.sector is not None and call.sectors.filter(pk=profile.sector.pk).exists():
        score += 20
        reasons.append(f"Sektör uyumlu: {profile.sector.name_tr}")
    if profile.theme is not None and call.themes.filter(pk=profile.theme.pk).exists():
        score += 15
        reasons.append(f"Tema uyumlu: {profile.theme.name_tr}")
    if profile.program_type is not None and call.program_types.filter(pk=profile.program_type.pk).exists():
        score += 12
        reasons.append(f"Program türü uyumlu: {profile.program_type.name_tr}")
    if profile.query:
        haystack = " ".join([call.title, call.summary, call.purpose, call.eligibility_text]).casefold()
        query_tokens = [token for token in profile.query.casefold().split() if len(token) >= 2]
        matched_tokens = [token for token in query_tokens if token in haystack]
        if matched_tokens:
            score += min(len(matched_tokens) * 8, 24)
            reasons.append("Arama metni çağrı içeriğiyle örtüşüyor")
    if call.availability_status == GrantCall.AvailabilityStatus.CLOSING_SOON:
        score += 5
        reasons.append("Son tarih yaklaşıyor")
    if call.availability_status == GrantCall.AvailabilityStatus.OPEN:
        score += 4
        reasons.append("Başvuruya açık")

    return MatchedCall(call=call, score=score, reasons=reasons[:4], url=build_call_detail_path(call))
