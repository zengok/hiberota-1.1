from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from automation.pipeline.persistence import resolve_audience_keys
from automation.pipeline.taxonomy_rules import infer_audience_keys_for_call
from django.db.models import QuerySet

from apps.calls.models import GrantCall


class AudienceGapReason(StrEnum):
    BACKFILL_CANDIDATE = "backfill_candidate"
    SOURCE_HINT_ONLY = "source_hint_only"
    MISSING_ELIGIBILITY_TEXT = "missing_eligibility_text"
    SPARSE_CALL_TEXT = "sparse_call_text"
    NO_RULE_MATCH = "no_rule_match"


@dataclass(frozen=True)
class AudienceGapEntry:
    call: GrantCall
    reason: AudienceGapReason
    inferred_keys: tuple[str, ...]
    source_hint_keys: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class AudienceGapReport:
    entries: tuple[AudienceGapEntry, ...]

    def counts_by_reason(self) -> dict[AudienceGapReason, int]:
        counts = {reason: 0 for reason in AudienceGapReason}
        for entry in self.entries:
            counts[entry.reason] += 1
        return counts

    def entries_for(self, reason: AudienceGapReason | None) -> tuple[AudienceGapEntry, ...]:
        if reason is None:
            return self.entries
        return tuple(entry for entry in self.entries if entry.reason == reason)


def build_audience_gap_report(*, queryset: QuerySet[GrantCall] | None = None) -> AudienceGapReport:
    calls = _call_queryset(queryset)
    return AudienceGapReport(entries=tuple(_classify_call(call) for call in calls))


def _call_queryset(queryset: QuerySet[GrantCall] | None) -> QuerySet[GrantCall]:
    base_queryset = queryset if queryset is not None else GrantCall.objects.all()
    return (
        base_queryset.filter(audiences__isnull=True)
        .select_related("source", "source__institution", "institution")
        .order_by("id")
        .distinct()
    )


def _classify_call(call: GrantCall) -> AudienceGapEntry:
    inferred_keys = resolve_audience_keys(infer_audience_keys_for_call(call))
    source_hint_keys = _source_hint_keys(call)
    if inferred_keys:
        return AudienceGapEntry(
            call=call,
            reason=AudienceGapReason.BACKFILL_CANDIDATE,
            inferred_keys=inferred_keys,
            source_hint_keys=source_hint_keys,
            note="call text matches existing taxonomy rules",
        )
    if source_hint_keys:
        return AudienceGapEntry(
            call=call,
            reason=AudienceGapReason.SOURCE_HINT_ONLY,
            inferred_keys=(),
            source_hint_keys=source_hint_keys,
            note="source has audience_hints, but call text has no explicit audience signal",
        )
    if not call.eligibility_text.strip():
        return AudienceGapEntry(
            call=call,
            reason=AudienceGapReason.MISSING_ELIGIBILITY_TEXT,
            inferred_keys=(),
            source_hint_keys=(),
            note="eligibility text is missing, so audience cannot be inferred safely",
        )
    if _visible_text_length(call) < 160:
        return AudienceGapEntry(
            call=call,
            reason=AudienceGapReason.SPARSE_CALL_TEXT,
            inferred_keys=(),
            source_hint_keys=(),
            note="call text is too sparse for reliable rule-based inference",
        )
    return AudienceGapEntry(
        call=call,
        reason=AudienceGapReason.NO_RULE_MATCH,
        inferred_keys=(),
        source_hint_keys=(),
        note="call text is present, but no conservative audience rule matched",
    )


def _source_hint_keys(call: GrantCall) -> tuple[str, ...]:
    raw_hints = call.source.config_json.get("audience_hints", [])
    if not isinstance(raw_hints, list):
        return ()
    return resolve_audience_keys(tuple(str(key).strip() for key in raw_hints if str(key).strip()))


def _visible_text_length(call: GrantCall) -> int:
    return len(
        " ".join(
            (
                call.title,
                call.summary,
                call.purpose,
                call.eligibility_text,
                call.conditions_text,
                call.funding_text,
                call.application_process_text,
            )
        ).strip()
    )
