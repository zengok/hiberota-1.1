from __future__ import annotations

from dataclasses import dataclass

from automation.adapters.contracts import ParsedCall


@dataclass(frozen=True, slots=True)
class ConfidenceDecision:
    score: int
    requires_review: bool
    reason_codes: tuple[str, ...]


def calculate_confidence(call: ParsedCall) -> ConfidenceDecision:
    score = 0
    reasons: list[str] = []

    score += _points(bool(call.title), 15, "missing_title", reasons)
    score += _points(bool(call.official_url), 10, "missing_official_url", reasons)
    score += _points(bool(call.institution_name), 10, "missing_institution", reasons)
    score += _points(bool(call.audience_keys), 10, "missing_audience", reasons)
    score += _points(bool(call.application_open_at or call.deadline_at), 20, "missing_dates", reasons)
    score += _points(bool(call.summary or call.purpose), 10, "missing_summary", reasons)
    score += _points(bool(call.funding_text or call.funding_min or call.funding_max), 10, "missing_funding", reasons)
    score += _points(bool(call.country_codes), 5, "missing_country", reasons)
    score += _points(bool(call.eligibility_text), 5, "missing_eligibility", reasons)
    score += _points(bool(call.evidence), 5, "missing_evidence", reasons)

    requires_review = score < 85 or "missing_official_url" in reasons or "missing_dates" in reasons
    return ConfidenceDecision(score=score, requires_review=requires_review, reason_codes=tuple(reasons))


def _points(condition: bool, value: int, reason: str, reasons: list[str]) -> int:
    if condition:
        return value
    reasons.append(reason)
    return 0
