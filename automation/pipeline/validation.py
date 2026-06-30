from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from apps.ingestion.models import ReviewItem

from automation.adapters.contracts import ParsedCall

PORTAL_SOURCE_CATEGORIES = {
    "agency_portal",
    "application_portal",
    "central_portal",
    "foundation_portal",
    "multilateral_portal",
    "programme_portal",
    "regional_agency_portal",
    "regional_portal",
}


class ValidationSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    reason_code: str
    severity: ValidationSeverity
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def requires_review(self) -> bool:
        return bool(self.issues)


def validate_parsed_call(call: ParsedCall) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if not call.title.strip():
        issues.append(
            ValidationIssue(
                reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                severity=ValidationSeverity.HIGH,
                message="title is required",
            )
        )
    if not call.official_url.strip():
        issues.append(
            ValidationIssue(
                reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                severity=ValidationSeverity.HIGH,
                message="official_url is required for auto-publish",
            )
        )
    if not call.canonical_source_url.strip():
        issues.append(
            ValidationIssue(
                reason_code=ReviewItem.ReasonCode.MISSING_REQUIRED_FIELD,
                severity=ValidationSeverity.HIGH,
                message="canonical_source_url is required",
            )
        )
    if call.application_open_at is not None and call.deadline_at is not None:
        if call.deadline_at < call.application_open_at:
            issues.append(
                ValidationIssue(
                    reason_code=ReviewItem.ReasonCode.DEADLINE_CONFLICT,
                    severity=ValidationSeverity.HIGH,
                    message="deadline_at is before application_open_at",
                )
            )
    if str(call.raw_metadata.get("source_status", "")).casefold() == "closed":
        issues.append(
            ValidationIssue(
                reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED,
                severity=ValidationSeverity.MEDIUM,
                message="source marks this call as closed",
            )
        )
    source_category = str(call.raw_metadata.get("source_category", ""))
    item_kind = str(call.raw_metadata.get("item_kind", ""))
    if is_portal_source_category(source_category) and item_kind != "detail":
        issues.append(
            ValidationIssue(
                reason_code=ReviewItem.ReasonCode.SOURCE_RESTRICTED,
                severity=ValidationSeverity.MEDIUM,
                message=f"{source_category} requires detail discovery before public publishing",
            )
        )
    return ValidationResult(issues=tuple(issues))


def is_portal_source_category(source_category: str) -> bool:
    return source_category in PORTAL_SOURCE_CATEGORIES or source_category.endswith("_portal")
