from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from django.db.models import QuerySet

from apps.calls.fingerprints import normalize_fingerprint_text
from apps.calls.models import GrantCall
from apps.calls.services import calculate_availability_status

HISTORICAL_TITLE_KEYWORDS = ("kapanan", "kapandı", "kapandi", "geçmiş", "gecmis", "arşiv", "arsiv", "tamamlanan")


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    key: str
    call_ids: tuple[int, ...]
    titles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AvailabilityMismatch:
    call_id: int
    title: str
    current_status: str
    expected_status: str


@dataclass(frozen=True, slots=True)
class FalseOpenCandidate:
    call_id: int
    title: str
    source_key: str
    reason: str


@dataclass(frozen=True, slots=True)
class CallDataQualityReport:
    checked_calls: int
    duplicate_candidates: tuple[DuplicateCandidate, ...]
    availability_mismatches: tuple[AvailabilityMismatch, ...]
    false_open_candidates: tuple[FalseOpenCandidate, ...]

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicate_candidates or self.availability_mismatches or self.false_open_candidates)


def build_call_data_quality_report(
    *,
    queryset: QuerySet[GrantCall] | None = None,
    now: datetime | None = None,
) -> CallDataQualityReport:
    base_queryset = queryset if queryset is not None else GrantCall.objects.all()
    calls = list(base_queryset.select_related("institution", "source").order_by("id"))
    return CallDataQualityReport(
        checked_calls=len(calls),
        duplicate_candidates=_find_semantic_duplicates(calls),
        availability_mismatches=_find_availability_mismatches(calls, now=now),
        false_open_candidates=_find_false_open_candidates(calls, now=now),
    )


def _find_semantic_duplicates(calls: Iterable[GrantCall]) -> tuple[DuplicateCandidate, ...]:
    groups: dict[str, list[GrantCall]] = defaultdict(list)
    for call in calls:
        deadline_part = call.deadline_at.date().isoformat() if call.deadline_at else "no-deadline"
        normalized_title = normalize_fingerprint_text(call.title)
        key = f"institution:{call.institution_id}|title:{normalized_title}|deadline:{deadline_part}"
        groups[key].append(call)

    duplicate_candidates = []
    for key, grouped_calls in groups.items():
        distinct_urls = {call.canonical_source_url.strip().lower() for call in grouped_calls}
        if len(grouped_calls) > 1 and len(distinct_urls) > 1:
            duplicate_candidates.append(
                DuplicateCandidate(
                    key=key,
                    call_ids=tuple(call.id for call in grouped_calls),
                    titles=tuple(call.title for call in grouped_calls),
                )
            )

    return tuple(sorted(duplicate_candidates, key=lambda candidate: candidate.key))


def _find_availability_mismatches(
    calls: Iterable[GrantCall],
    *,
    now: datetime | None,
) -> tuple[AvailabilityMismatch, ...]:
    mismatches = []
    for call in calls:
        expected_status = calculate_availability_status(
            application_open_at=call.application_open_at,
            deadline_at=call.deadline_at,
            now=now,
        )
        if call.availability_status != expected_status:
            mismatches.append(
                AvailabilityMismatch(
                    call_id=call.id,
                    title=call.title,
                    current_status=call.availability_status,
                    expected_status=expected_status,
                )
            )
    return tuple(mismatches)


def _find_false_open_candidates(
    calls: Iterable[GrantCall],
    *,
    now: datetime | None,
) -> tuple[FalseOpenCandidate, ...]:
    reference_year = (now or datetime.now()).year
    candidates = []
    for call in calls:
        if not _is_false_open_candidate(call, reference_year=reference_year):
            continue
        candidates.append(
            FalseOpenCandidate(
                call_id=call.id,
                title=call.title,
                source_key=call.source.source_key or "",
                reason=_false_open_reason(call, reference_year=reference_year),
            )
        )
    return tuple(candidates)


def _is_false_open_candidate(call: GrantCall, *, reference_year: int) -> bool:
    if call.workflow_status != GrantCall.WorkflowStatus.PUBLISHED:
        return False
    if call.availability_status != GrantCall.AvailabilityStatus.OPEN:
        return False
    if call.deadline_at is not None:
        return False
    if call.eligibility_text.strip():
        return False
    if call.audiences.exists():
        return False
    return _looks_historical_or_closed(call.title, reference_year=reference_year)


def _false_open_reason(call: GrantCall, *, reference_year: int) -> str:
    title = call.title.casefold()
    for keyword in HISTORICAL_TITLE_KEYWORDS:
        if keyword in title:
            return f"title contains historical/closed keyword: {keyword}"
    year = _first_year(call.title)
    if year is not None and year < reference_year:
        return f"title year {year} is before reference year {reference_year} and required call fields are missing"
    return "published open call lacks deadline, eligibility, audience, and has historical title signals"


def _looks_historical_or_closed(title: str, *, reference_year: int) -> bool:
    normalised = title.casefold()
    if any(keyword in normalised for keyword in HISTORICAL_TITLE_KEYWORDS):
        return True
    year = _first_year(title)
    return year is not None and year < reference_year


def _first_year(title: str) -> int | None:
    match = re.search(r"\b(20[0-9]{2})\b", title)
    if match is None:
        return None
    return int(match.group(1))
