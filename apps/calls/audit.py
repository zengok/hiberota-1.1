from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from django.db.models import QuerySet

from apps.calls.fingerprints import normalize_fingerprint_text
from apps.calls.models import GrantCall
from apps.calls.services import calculate_availability_status


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
class CallDataQualityReport:
    checked_calls: int
    duplicate_candidates: tuple[DuplicateCandidate, ...]
    availability_mismatches: tuple[AvailabilityMismatch, ...]

    @property
    def has_issues(self) -> bool:
        return bool(self.duplicate_candidates or self.availability_mismatches)


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
