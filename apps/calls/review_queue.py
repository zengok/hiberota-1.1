from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from django.db.models import Prefetch, QuerySet
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.ingestion.models import FieldEvidence, ReviewItem


class ReviewQueueCategory(StrEnum):
    CLOSED_SOURCE = "closed_source"
    GUIDANCE_PAGE = "guidance_page"
    PUBLISH_CANDIDATE = "publish_candidate"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"


@dataclass(frozen=True)
class ReviewQueueEntry:
    call: GrantCall
    category: ReviewQueueCategory
    reason: str
    open_reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ReviewQueueReport:
    entries: tuple[ReviewQueueEntry, ...]

    def counts_by_category(self) -> dict[ReviewQueueCategory, int]:
        counts = {category: 0 for category in ReviewQueueCategory}
        for entry in self.entries:
            counts[entry.category] += 1
        return counts

    def entries_for(self, category: ReviewQueueCategory | None) -> tuple[ReviewQueueEntry, ...]:
        if category is None:
            return self.entries
        return tuple(entry for entry in self.entries if entry.category == category)


GUIDANCE_KEYWORDS = (
    "application-process",
    "applying-for-funding",
    "applying-funding",
    "funding/applying",
    "funding-stages",
    "manage-your-grant",
    "managing-funds",
    "why-applications-dont-always-succeed",
    "about",
    "contact",
    "eligibility",
    "faq",
    "frequently-asked-questions",
    "guidance",
    "guide",
    "how-to-apply",
    "information",
    "instructions",
    "manual",
    "nasıl başvurulur",
    "nasıl destek alınır",
    "alım ilanı",
    "ana sayfa",
    "arama",
    "arşiv",
    "bağlantı gezgini",
    "başarılı proje",
    "başvuru bilgileri",
    "başvuru için gerekli belgeler",
    "başvuru sonuç",
    "bölge planı",
    "çalışma program",
    "orta vadeli program",
    "policy",
    "procedure",
    "resources",
    "değerlendirme sonuç",
    "diğer döküman",
    "doküman",
    "döküman",
    "sıkça sorulan",
    "s.s.s",
    "terms",
    "sss",
    "desteklenmiş proje",
    "haber / duyuru",
    "haberler",
    "ihale",
    "içerikler",
    "imzalandı",
    "imzalar atıldı",
    "ilanına çıkıldı",
    "lanına çıkıldı",
    "kays kılavuzu",
    "kurumsal",
    "personel al",
    "proje ihaleleri",
    "proje uygulama",
    "projeler veri tabanı",
    "rapor",
    "satın alma",
    "sonuçları",
    "sonuç odaklı",
    "sözleşme",
    "tamamlandı",
    "yatırım destek ofis",
)

EXACT_GUIDANCE_TITLES = {
    "ana sayfa",
    "arama",
    "başarılı projeler",
    "başvuru bilgileri",
    "başvuru çağrı ilanları",
    "başvuru çağrı rehberleri",
    "çalışma programları",
    "destek araçlarımız",
    "destek istatistikleri",
    "destek programları",
    "destek programları arşivi",
    "destek türleri",
    "destek ve duyurular",
    "destekler",
    "diğer kurumların destek programları",
    "doküman merkezi",
    "duyurular",
    "haber / duyuru",
    "haberler",
    "ihale ilanları",
    "içerikler",
    "krediler",
    "kurumsal",
    "mali destek projeleri",
    "orta vadeli programlar",
    "proje hazırlama eğitim talepleri",
    "proje ihaleleri",
    "proje uygulama",
    "proje uygulama süreci",
    "projeler veri tabanı",
    "tamamlanan projeler arşivi",
    "teknik destek projeleri",
    "yatırım destek",
    "yatırım destek ofisleri",
}

PUBLISHABLE_STATUSES = (
    GrantCall.AvailabilityStatus.OPEN,
    GrantCall.AvailabilityStatus.CLOSING_SOON,
    GrantCall.AvailabilityStatus.UPCOMING,
)


def build_review_queue_report(
    *,
    now: datetime | None = None,
    min_publish_confidence: int = 60,
    queryset: QuerySet[GrantCall] | None = None,
) -> ReviewQueueReport:
    reference_time = now or timezone.now()
    calls = _review_call_queryset(queryset)
    entries = tuple(
        _classify_call(call, now=reference_time, min_publish_confidence=min_publish_confidence) for call in calls
    )
    return ReviewQueueReport(entries=entries)


def _review_call_queryset(queryset: QuerySet[GrantCall] | None) -> QuerySet[GrantCall]:
    base_queryset = queryset if queryset is not None else GrantCall.objects.all()
    open_review_items = ReviewItem.objects.filter(
        status__in=(ReviewItem.Status.OPEN, ReviewItem.Status.IN_PROGRESS)
    ).order_by("reason_code")
    source_status_evidence = FieldEvidence.objects.filter(field_name="source_status").order_by("-fetched_at")
    return (
        base_queryset.filter(workflow_status=GrantCall.WorkflowStatus.REVIEW)
        .select_related("source", "institution")
        .prefetch_related(
            Prefetch("review_items", queryset=open_review_items, to_attr="open_review_items"),
            Prefetch("field_evidence", queryset=source_status_evidence, to_attr="source_status_evidence"),
        )
        .order_by("id")
    )


def _classify_call(call: GrantCall, *, now: datetime, min_publish_confidence: int) -> ReviewQueueEntry:
    reason_codes = _open_reason_codes(call)
    source_status = _source_status(call)
    if _is_closed(call=call, now=now, source_status=source_status, reason_codes=reason_codes):
        return ReviewQueueEntry(
            call=call,
            category=ReviewQueueCategory.CLOSED_SOURCE,
            reason=_closed_reason(call=call, now=now, source_status=source_status),
            open_reason_codes=reason_codes,
        )
    if _looks_like_guidance_page(call):
        return ReviewQueueEntry(
            call=call,
            category=ReviewQueueCategory.GUIDANCE_PAGE,
            reason="title or URL matches guidance/general information patterns",
            open_reason_codes=reason_codes,
        )
    if _is_publish_candidate(call=call, now=now, reason_codes=reason_codes, min_confidence=min_publish_confidence):
        return ReviewQueueEntry(
            call=call,
            category=ReviewQueueCategory.PUBLISH_CANDIDATE,
            reason="open source, usable official URL, and only low-confidence review remains",
            open_reason_codes=reason_codes,
        )
    return ReviewQueueEntry(
        call=call,
        category=ReviewQueueCategory.NEEDS_MANUAL_REVIEW,
        reason="requires operator review before publish or reject",
        open_reason_codes=reason_codes,
    )


def _open_reason_codes(call: GrantCall) -> tuple[str, ...]:
    review_items = getattr(call, "open_review_items", ())
    return tuple(dict.fromkeys(str(review.reason_code) for review in review_items))


def _source_status(call: GrantCall) -> str:
    evidence_items = getattr(call, "source_status_evidence", ())
    for evidence in evidence_items:
        source_status = evidence.source_excerpt.strip().lower()
        if source_status:
            return source_status
    return ""


def _is_closed(*, call: GrantCall, now: datetime, source_status: str, reason_codes: tuple[str, ...]) -> bool:
    if source_status == "closed":
        return True
    if call.availability_status == GrantCall.AvailabilityStatus.CLOSED:
        return True
    if call.deadline_at and call.deadline_at <= now:
        return True
    return ReviewItem.ReasonCode.SOURCE_RESTRICTED in reason_codes


def _closed_reason(*, call: GrantCall, now: datetime, source_status: str) -> str:
    if source_status == "closed":
        return "official source status is closed"
    if call.availability_status == GrantCall.AvailabilityStatus.CLOSED:
        return "call availability is closed"
    if call.deadline_at and call.deadline_at <= now:
        return "deadline is in the past"
    return "open review item marks the source as restricted"


def _looks_like_guidance_page(call: GrantCall) -> bool:
    title = call.title.casefold().strip()
    if title in EXACT_GUIDANCE_TITLES:
        return True
    haystack = " ".join(
        (
            call.title,
            call.official_url,
            call.canonical_source_url,
            call.summary,
        )
    ).casefold()
    return any(keyword in haystack for keyword in GUIDANCE_KEYWORDS)


def _is_publish_candidate(
    *,
    call: GrantCall,
    now: datetime,
    reason_codes: tuple[str, ...],
    min_confidence: int,
) -> bool:
    if not call.official_url or not call.canonical_source_url:
        return False
    if call.confidence_score < min_confidence:
        return False
    if call.availability_status not in PUBLISHABLE_STATUSES:
        return False
    if call.deadline_at and call.deadline_at <= now:
        return False
    blocking_reasons = set(reason_codes) - {ReviewItem.ReasonCode.LOW_CONFIDENCE}
    return not blocking_reasons


def parse_review_queue_category(value: str) -> ReviewQueueCategory:
    try:
        return ReviewQueueCategory(value)
    except ValueError as exc:
        allowed = ", ".join(category.value for category in ReviewQueueCategory)
        raise ValueError(f"Invalid category '{value}'. Allowed values: {allowed}.") from exc


def category_values() -> Iterable[str]:
    return (category.value for category in ReviewQueueCategory)
