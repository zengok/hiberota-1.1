from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from django.core.paginator import Page, Paginator
from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.http import QueryDict
from django.urls import reverse

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.taxonomy.models import AudienceType, ProgramType, Region, Sector, Theme

CALLS_PER_PAGE = 12

SORT_OPTIONS = {
    "yeni": ("-first_seen_at", "Yeni yakalananlar"),
    "eski": ("first_seen_at", "Eski yakalananlar"),
    "son-tarih-yakin": ("deadline_at", "Son tarihi en yakın"),
    "son-tarih-uzak": ("-deadline_at", "Son tarihi en uzak"),
    "acilis-yeni": ("-application_open_at", "Açılış tarihi yeni"),
    "acilis-eski": ("application_open_at", "Açılış tarihi eski"),
}

STATUS_LABELS: dict[str, str] = {
    GrantCall.AvailabilityStatus.UPCOMING: "Gelecek",
    GrantCall.AvailabilityStatus.OPEN: "Açık",
    GrantCall.AvailabilityStatus.CLOSING_SOON: "Kapanmak üzere",
    GrantCall.AvailabilityStatus.CLOSED: "Kapalı",
}

AUDIENCE_LABELS: dict[str, str] = {
    "student": "Öğrenci",
    "graduate_student": "Lisansüstü Öğrenci",
    "academic": "Akademisyen",
    "researcher": "Araştırmacı",
    "entrepreneur": "Girişimci",
    "startup": "Girişim",
    "sme": "KOBİ",
    "company": "Şirket",
    "ngo": "STK",
    "municipality": "Belediye",
    "public_institution": "Kamu Kurumu",
    "consortium": "Konsorsiyum",
}

STATUS_SORT_ORDER = Case(
    When(availability_status=GrantCall.AvailabilityStatus.CLOSING_SOON, then=Value(0)),
    When(availability_status=GrantCall.AvailabilityStatus.OPEN, then=Value(1)),
    When(availability_status=GrantCall.AvailabilityStatus.UPCOMING, then=Value(2)),
    When(availability_status=GrantCall.AvailabilityStatus.UNKNOWN, then=Value(3)),
    When(availability_status=GrantCall.AvailabilityStatus.CLOSED, then=Value(4)),
    default=Value(5),
    output_field=IntegerField(),
)

FILTER_LABELS = {
    "q": "Arama",
    "kapsam": "Kapsam",
    "ulke": "Ülke",
    "avrupa": "Avrupa",
    "bolge": "Bölge",
    "kurum": "Kurum",
    "hedef": "Hedef kitle",
    "sektor": "Sektör",
    "tema": "Tema",
    "program": "Program türü",
    "durum": "Durum",
    "para_birimi": "Para birimi",
    "yayin_baslangic": "Yayın başlangıcı",
    "yayin_bitis": "Yayın bitişi",
    "acilis_baslangic": "Açılış başlangıcı",
    "acilis_bitis": "Açılış bitişi",
    "son_tarih_baslangic": "Son tarih başlangıcı",
    "son_tarih_bitis": "Son tarih bitişi",
    "siralama": "Sıralama",
}


@dataclass(frozen=True)
class ActiveFilter:
    key: str
    label: str
    value: str
    remove_url: str


def get_call_list_context(params: QueryDict) -> dict[str, Any]:
    filtered_calls = apply_call_filters(_published_calls(), params)
    sorted_calls = apply_call_sort(filtered_calls, params.get("siralama", "yeni"))
    page = paginate_calls(sorted_calls, params)
    active_filters = build_active_filters(params)

    return {
        "page_title": "Hibe ve Fon Çağrıları | HibeRota",
        "meta_description": "Yayınlanmış hibe, fon ve proje çağrılarını ülke, kurum, hedef kitle ve tarihe göre süzün.",
        "canonical_path": "/cagrilar/",
        "robots": "noindex,follow" if active_filters else "index,follow",
        "calls_page": page,
        "result_count": filtered_calls.count(),
        "active_filters": active_filters,
        "filters": build_filter_options(params),
        "sort_options": SORT_OPTIONS,
        "current_sort": params.get("siralama", "yeni"),
        "sort_hidden_fields": _query_items(params, exclude=["siralama", "sayfa"]),
    }


def _published_calls() -> QuerySet[GrantCall]:
    return (
        GrantCall.objects.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .select_related("institution")
        .prefetch_related("countries", "audiences")
    )


def apply_call_filters(calls: QuerySet[GrantCall], params: QueryDict) -> QuerySet[GrantCall]:
    query = params.get("q", "").strip()
    if query:
        calls = calls.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(institution__name__icontains=query)
            | Q(countries__name_tr__icontains=query)
        )

    if country_code := params.get("ulke"):
        calls = calls.filter(countries__code=country_code.upper())

    if params.get("kapsam") == "dunya":
        calls = calls.exclude(countries__code="TR")

    if params.get("avrupa") == "1":
        calls = calls.filter(countries__is_europe=True)

    if region_key := params.get("bolge"):
        calls = calls.filter(Q(regions__key=region_key) | Q(countries__region_code=region_key))

    if institution_slug := params.get("kurum"):
        calls = calls.filter(institution__slug=institution_slug)

    audience_keys = [value.strip() for value in params.getlist("hedef") if value.strip()]
    if audience_keys:
        calls = calls.filter(audiences__key__in=audience_keys)

    if sector_key := params.get("sektor"):
        calls = calls.filter(sectors__key=sector_key)

    if theme_key := params.get("tema"):
        calls = calls.filter(themes__key=theme_key)

    if program_key := params.get("program"):
        calls = calls.filter(program_types__key=program_key)

    if status := params.get("durum"):
        calls = calls.filter(availability_status=status)

    if currency := params.get("para_birimi"):
        calls = calls.filter(currency=currency.upper())

    calls = apply_date_range(calls, "published_at", params.get("yayin_baslangic"), params.get("yayin_bitis"))
    calls = apply_date_range(calls, "application_open_at", params.get("acilis_baslangic"), params.get("acilis_bitis"))
    calls = apply_date_range(calls, "deadline_at", params.get("son_tarih_baslangic"), params.get("son_tarih_bitis"))

    return calls.distinct()


def apply_date_range(
    calls: QuerySet[GrantCall],
    field_name: str,
    starts_at: str | None,
    ends_at: str | None,
) -> QuerySet[GrantCall]:
    if starts_at and _is_iso_date(starts_at):
        calls = calls.filter(**{f"{field_name}__date__gte": starts_at})
    if ends_at and _is_iso_date(ends_at):
        calls = calls.filter(**{f"{field_name}__date__lte": ends_at})
    return calls


def apply_call_sort(calls: QuerySet[GrantCall], sort_key: str) -> QuerySet[GrantCall]:
    order_field = SORT_OPTIONS.get(sort_key, SORT_OPTIONS["yeni"])[0]
    calls = calls.annotate(_status_sort_order=STATUS_SORT_ORDER)
    if order_field.lstrip("-") in {"deadline_at", "application_open_at"}:
        return calls.order_by("_status_sort_order", f"{order_field}", "-first_seen_at")
    return calls.order_by("_status_sort_order", order_field)


def paginate_calls(calls: QuerySet[GrantCall], params: QueryDict) -> Page[GrantCall]:
    paginator = Paginator(calls, CALLS_PER_PAGE)
    return paginator.get_page(params.get("sayfa", "1"))


def build_filter_options(params: QueryDict) -> dict[str, Any]:
    return {
        "values": {key: params.get(key, "") for key in FILTER_LABELS},
        "countries": Country.objects.filter(is_active=True).order_by("name_tr"),
        "regions": Region.objects.filter(is_active=True).order_by("name_tr"),
        "institutions": Institution.objects.filter(is_active=True).order_by("name"),
        "audiences": AudienceType.objects.filter(is_active=True).order_by("name_tr"),
        "sectors": Sector.objects.filter(is_active=True).order_by("name_tr"),
        "themes": Theme.objects.filter(is_active=True).order_by("name_tr"),
        "program_types": ProgramType.objects.filter(is_active=True).order_by("name_tr"),
        "statuses": STATUS_LABELS,
        "currencies": _available_currencies(),
        "quick_turkey_url": _replace_query(params, {"ulke": "TR"}, remove=["sayfa"]),
        "quick_europe_url": _replace_query(params, {"avrupa": "1"}, remove=["sayfa"]),
    }


def build_active_filters(params: QueryDict) -> list[ActiveFilter]:
    active_filters = []
    for key, label in FILTER_LABELS.items():
        if key == "hedef":
            values = [value.strip() for value in params.getlist(key) if value.strip()]
            if not values:
                continue
            active_filters.append(
                ActiveFilter(
                    key=key,
                    label=label,
                    value=", ".join(_display_filter_value(key, value) for value in values),
                    remove_url=_replace_query(params, {}, remove=[key, "sayfa"]),
                )
            )
            continue
        value = params.get(key, "").strip()
        if not value or key == "siralama" and value == "yeni":
            continue
        active_filters.append(
            ActiveFilter(
                key=key,
                label=label,
                value=_display_filter_value(key, value),
                remove_url=_replace_query(params, {}, remove=[key, "sayfa"]),
            )
        )
    return active_filters


def build_page_url(params: QueryDict, page_number: int) -> str:
    return _replace_query(params, {"sayfa": str(page_number)}, remove=[])


def _available_currencies() -> list[str]:
    return list(
        GrantCall.objects.filter(workflow_status=GrantCall.WorkflowStatus.PUBLISHED)
        .exclude(currency="")
        .order_by("currency")
        .values_list("currency", flat=True)
        .distinct()
    )


def _display_filter_value(key: str, value: str) -> str:
    if key == "durum":
        return STATUS_LABELS.get(value, value)
    if key == "siralama":
        return SORT_OPTIONS.get(value, SORT_OPTIONS["yeni"])[1]
    if key == "avrupa" and value == "1":
        return "Avrupa"
    if key == "kapsam" and value == "dunya":
        return "Dünya"
    if key == "hedef":
        return AUDIENCE_LABELS.get(value, value)
    return value


def _replace_query(params: QueryDict, updates: dict[str, str], remove: list[str]) -> str:
    query = params.copy()
    for key in remove:
        query.pop(key, None)
    for key, value in updates.items():
        query[key] = value
    encoded = query.urlencode()
    base_path = reverse("call-list")
    return f"{base_path}?{encoded}" if encoded else base_path


def _query_items(params: QueryDict, exclude: list[str]) -> list[tuple[str, str]]:
    items = []
    for key in params:
        if key in exclude:
            continue
        for value in params.getlist(key):
            items.append((key, value))
    return items


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
