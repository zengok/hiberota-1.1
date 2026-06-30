from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from apps.sources.models import Source

REQUIRED_COLUMNS = frozenset(
    {
        "source_key",
        "institution_name",
        "country_code",
        "source_name",
        "base_url",
        "listing_url",
        "source_type",
        "adapter_key",
        "crawl_interval_minutes",
        "language_codes",
        "robots_status",
        "terms_status",
        "enabled",
    }
)

OPTIONAL_COLUMNS = frozenset(
    {
        "institution_short_name",
        "region_code",
        "audience_hints",
        "robots_checked_at",
        "api_docs_url",
        "rss_feed_url",
        "contact_url",
        "notes",
        "config_json",
    }
)

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-|BEGIN (?:RSA|OPENSSH|PRIVATE) KEY)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class CatalogValidationIssue:
    row_number: int
    column: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CatalogValidationResult:
    is_valid: bool
    issues: tuple[CatalogValidationIssue, ...] = ()
    warnings: tuple[CatalogValidationIssue, ...] = ()
    row_count: int = 0
    missing_columns: tuple[str, ...] = ()
    unknown_columns: tuple[str, ...] = ()


@dataclass(slots=True)
class CatalogValidationBuilder:
    issues: list[CatalogValidationIssue] = field(default_factory=list)
    warnings: list[CatalogValidationIssue] = field(default_factory=list)

    def add_issue(self, row_number: int, column: str, code: str, message: str) -> None:
        self.issues.append(CatalogValidationIssue(row_number, column, code, message))

    def add_warning(self, row_number: int, column: str, code: str, message: str) -> None:
        self.warnings.append(CatalogValidationIssue(row_number, column, code, message))


def validate_source_catalog_rows(rows: list[dict[str, Any]], headers: list[str]) -> CatalogValidationResult:
    builder = CatalogValidationBuilder()
    header_set = set(headers)
    allowed_columns = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
    missing_columns = tuple(sorted(REQUIRED_COLUMNS - header_set))
    unknown_columns = tuple(sorted(header_set - allowed_columns))

    for column in missing_columns:
        builder.add_issue(1, column, "missing_column", "Required source catalog column is missing.")

    source_keys = [str(row.get("source_key", "")).strip() for row in rows]
    duplicate_keys = {key for key, count in Counter(source_keys).items() if key and count > 1}

    for index, row in enumerate(rows, start=2):
        _validate_required_values(row, index, builder)
        _validate_source_key(row, index, builder)
        _validate_enums(row, index, builder)
        _validate_urls(row, index, builder)
        _validate_country_code(row, index, builder)
        _validate_interval(row, index, builder)
        _validate_enabled(row, index, builder)
        _validate_config_json(row, index, builder)
        _validate_secret_patterns(row, index, builder)
        _validate_compliance_warnings(row, index, builder)

        source_key = str(row.get("source_key", "")).strip()
        if source_key in duplicate_keys:
            builder.add_issue(index, "source_key", "duplicate_source_key", "source_key must be unique.")

    return CatalogValidationResult(
        is_valid=not builder.issues,
        issues=tuple(builder.issues),
        warnings=tuple(builder.warnings),
        row_count=len(rows),
        missing_columns=missing_columns,
        unknown_columns=unknown_columns,
    )


def _validate_required_values(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    for column in REQUIRED_COLUMNS:
        if _blank(row.get(column)):
            builder.add_issue(row_number, column, "required", "Required value is missing.")


def _validate_source_key(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    value = str(row.get("source_key", "")).strip()
    if value and not re.fullmatch(r"[-a-zA-Z0-9_]+", value):
        builder.add_issue(row_number, "source_key", "invalid_source_key", "source_key must be slug-like.")


def _validate_enums(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    source_types = {choice.value for choice in Source.SourceType}
    robots_statuses = {choice.value for choice in Source.RobotsStatus}
    terms_statuses = {choice.value for choice in Source.TermsStatus}

    _validate_enum(row, row_number, builder, "source_type", source_types)
    _validate_enum(row, row_number, builder, "robots_status", robots_statuses)
    _validate_enum(row, row_number, builder, "terms_status", terms_statuses)


def _validate_enum(
    row: dict[str, Any],
    row_number: int,
    builder: CatalogValidationBuilder,
    column: str,
    allowed: set[str],
) -> None:
    value = str(row.get(column, "")).strip()
    if value and value not in allowed:
        builder.add_issue(row_number, column, "invalid_enum", f"Value must be one of: {', '.join(sorted(allowed))}.")


def _validate_urls(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    for column in ("base_url", "listing_url", "api_docs_url", "rss_feed_url", "contact_url"):
        value = row.get(column)
        if _blank(value):
            continue

        parsed = urlparse(str(value).strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            builder.add_issue(row_number, column, "invalid_url", "URL must use http or https and include a host.")


def _validate_country_code(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    value = str(row.get("country_code", "")).strip()
    if value and not re.fullmatch(r"[A-Z]{2}", value):
        builder.add_issue(row_number, "country_code", "invalid_country_code", "Country code must be ISO alpha-2.")


def _validate_interval(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    value = row.get("crawl_interval_minutes")
    if _blank(value):
        return

    try:
        interval = int(str(value))
    except (TypeError, ValueError):
        builder.add_issue(row_number, "crawl_interval_minutes", "invalid_interval", "Interval must be an integer.")
        return

    if interval < 15:
        builder.add_issue(
            row_number, "crawl_interval_minutes", "interval_too_low", "Interval must be at least 15 minutes."
        )


def _validate_enabled(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    value = row.get("enabled")
    if _blank(value):
        return

    if str(value).strip().lower() not in {"true", "false", "1", "0", "yes", "no"}:
        builder.add_issue(row_number, "enabled", "invalid_boolean", "Enabled must be a boolean-like value.")


def _validate_config_json(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    value = row.get("config_json")
    if _blank(value) or isinstance(value, dict):
        return

    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        builder.add_issue(row_number, "config_json", "invalid_json", "config_json must be valid JSON.")
        return

    if not isinstance(parsed, dict):
        builder.add_issue(row_number, "config_json", "invalid_json_object", "config_json must decode to an object.")


def _validate_secret_patterns(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    for column, value in row.items():
        if value is not None and SECRET_PATTERN.search(str(value)):
            builder.add_issue(
                row_number, column, "secret_like_value", "Secret-like value must not be stored in catalog."
            )


def _validate_compliance_warnings(row: dict[str, Any], row_number: int, builder: CatalogValidationBuilder) -> None:
    if (
        row.get("source_type") == Source.SourceType.HEADLESS
        and _blank(row.get("notes"))
        and _blank(row.get("config_json"))
    ):
        builder.add_warning(
            row_number, "source_type", "headless_needs_reason", "Headless sources need an explicit reason."
        )

    if row.get("robots_status") in {Source.RobotsStatus.RESTRICTED, Source.RobotsStatus.UNKNOWN}:
        builder.add_warning(
            row_number, "robots_status", "robots_review", "Robots status needs human review before crawling."
        )

    if row.get("terms_status") in {Source.TermsStatus.RESTRICTED, Source.TermsStatus.UNKNOWN}:
        builder.add_warning(
            row_number, "terms_status", "terms_review", "Terms status needs human review before crawling."
        )


def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""
