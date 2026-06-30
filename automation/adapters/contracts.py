from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

JsonMapping = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class CrawlContext:
    source_key: str
    source_url: str
    adapter_key: str
    config_version: int
    run_id: str | None = None
    fetched_at: datetime | None = None
    settings: JsonMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DiscoveredItem:
    source_url: str
    normalized_url: str
    title_hint: str = ""
    external_id: str = ""
    content_hash: str = ""
    metadata: JsonMapping = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FetchResult:
    item: DiscoveredItem
    final_url: str
    status_code: int
    content_type: str
    body_text: str
    fetched_at: datetime
    content_hash: str
    headers: Mapping[str, str] = field(default_factory=dict)
    evidence_excerpt: str = ""


@dataclass(frozen=True, slots=True)
class ParsedEvidence:
    field_name: str
    source_url: str
    source_excerpt: str
    selector_or_path: str = ""
    confidence: int = 0


@dataclass(frozen=True, slots=True)
class ParsedCall:
    title: str
    official_url: str
    canonical_source_url: str
    institution_name: str = ""
    external_id: str = ""
    summary: str = ""
    purpose: str = ""
    eligibility_text: str = ""
    conditions_text: str = ""
    duration_text: str = ""
    funding_text: str = ""
    application_process_text: str = ""
    contact_text: str = ""
    source_published_at: datetime | None = None
    application_open_at: datetime | None = None
    deadline_at: datetime | None = None
    deadline_timezone: str = "UTC"
    duration_min_months: int | None = None
    duration_max_months: int | None = None
    funding_min: Decimal | None = None
    funding_max: Decimal | None = None
    currency: str = ""
    funding_rate_percent: Decimal | None = None
    country_codes: tuple[str, ...] = ()
    audience_keys: tuple[str, ...] = ()
    sector_keys: tuple[str, ...] = ()
    theme_keys: tuple[str, ...] = ()
    program_type_keys: tuple[str, ...] = ()
    evidence: tuple[ParsedEvidence, ...] = ()
    raw_metadata: JsonMapping = field(default_factory=dict)


@runtime_checkable
class SourceAdapter(Protocol):
    key: str
    parser_version: str

    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        """Find candidate items without normalizing, validating, deduplicating, or publishing them."""

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        """Fetch one candidate detail using the controlled HTTP layer supplied by the caller."""

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        """Extract raw structured fields and evidence; downstream pipeline owns validation and publishing."""
