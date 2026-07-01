from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from html import unescape
from typing import Any, cast

from automation.adapters.contracts import CrawlContext, DiscoveredItem, FetchResult, ParsedCall, ParsedEvidence


class EuFundingTendersAdapter:
    key = "src-0022_eu_funding_v1"
    parser_version = "2026-07-01"

    def discover(self, context: CrawlContext) -> tuple[DiscoveredItem, ...]:
        return (DiscoveredItem(source_url=context.source_url, normalized_url=context.source_url),)

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        raise NotImplementedError("Controlled HTTP client supplies FetchResult in the pipeline.")

    def discover_from_fetch(self, result: FetchResult, context: CrawlContext) -> tuple[DiscoveredItem, ...]:
        data = json.loads(result.body_text)
        max_items = int(context.settings.get("max_detail_links") or 50)
        items: list[DiscoveredItem] = []
        for entry in data.get("results") or ():
            metadata = entry.get("metadata") if isinstance(entry, dict) else {}
            if not isinstance(metadata, dict):
                continue
            title = _first_value(metadata, "title") or str(entry.get("summary") or entry.get("content") or "")
            official_url = _first_value(metadata, "url") or str(entry.get("url") or "")
            identifier = _first_value(metadata, "identifier") or str(entry.get("reference") or "")
            source_status = _status_label(_first_value(metadata, "status"), _first_value(metadata, "sortStatus"))
            if not title or not official_url or source_status not in {"open", "upcoming"}:
                continue
            items.append(
                DiscoveredItem(
                    source_url=result.final_url,
                    normalized_url=official_url,
                    title_hint=title,
                    external_id=identifier,
                    metadata={
                        "kind": "detail",
                        "api_entry": entry,
                        "parse_without_fetch": True,
                        "source_status": source_status,
                        "application_open_at": _first_value(metadata, "startDate"),
                        "deadline_at": _first_value(metadata, "deadlineDate"),
                    },
                )
            )
            if len(items) >= max_items:
                break
        return tuple(items)

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        entry = result.item.metadata.get("api_entry")
        if not isinstance(entry, dict):
            entry = {}
        metadata = cast(dict[str, Any], entry.get("metadata")) if isinstance(entry.get("metadata"), dict) else {}

        title = result.item.title_hint or _first_value(metadata, "title") or str(entry.get("summary") or "")
        official_url = _first_value(metadata, "url") or result.final_url
        identifier = _first_value(metadata, "identifier") or result.item.external_id
        description = _clean_html(_first_value(metadata, "descriptionByte"))
        topic_conditions = _clean_html(_first_value(metadata, "topicConditions"))
        actions = _json_list(_first_value(metadata, "actions"))
        budget = _json_object(_first_value(metadata, "budgetOverview"))
        action = actions[0] if actions else {}

        open_at = _parse_utc_date(result.item.metadata.get("application_open_at")) or _parse_utc_date(
            _first_value(metadata, "startDate")
        )
        deadline_at = _parse_utc_date(result.item.metadata.get("deadline_at")) or _parse_utc_date(
            _first_value(metadata, "deadlineDate")
        )
        source_status = str(result.item.metadata.get("source_status") or "").strip() or _status_label(
            _first_value(metadata, "status"),
            _first_value(metadata, "sortStatus"),
        )
        funding_text = _funding_text(metadata=metadata, action=action, budget=budget, context=context)
        eligibility_text = _first_non_empty(
            _eligibility_excerpt(topic_conditions),
            (
                "Applicants must verify eligible country, consortium and action conditions on the official "
                "EU Funding & Tenders topic page."
            ),
        )
        summary = _first_non_empty(description, str(entry.get("summary") or ""), _first_value(metadata, "callTitle"))

        evidence = tuple(
            item
            for item in (
                _evidence("title", official_url, title, "metadata.title", 95),
                _evidence("summary", official_url, summary, "metadata.descriptionByte|summary", 90),
                _evidence(
                    "deadline",
                    official_url,
                    deadline_at.isoformat() if deadline_at else "",
                    "metadata.deadlineDate",
                    95,
                ),
                _evidence("source_status", official_url, source_status, "metadata.status|metadata.sortStatus", 95),
                _evidence("funding", official_url, funding_text, "metadata.budgetOverview|metadata.actions", 85),
                _evidence("eligibility", official_url, eligibility_text, "metadata.topicConditions", 80),
            )
            if item is not None
        )

        return ParsedCall(
            title=title,
            official_url=official_url,
            canonical_source_url=official_url,
            institution_name=str(context.settings.get("institution_name_override") or "Ufuk Avrupa Türkiye"),
            external_id=identifier,
            summary=summary,
            eligibility_text=eligibility_text,
            funding_text=funding_text,
            application_process_text=(
                "Applications are submitted through the official EU Funding & Tenders Portal submission service."
            ),
            application_open_at=open_at,
            deadline_at=deadline_at,
            country_codes=_tuple_setting(context.settings.get("country_codes_override") or ("EU", "TR")),
            audience_keys=_tuple_setting(context.settings.get("audience_hints") or ("researcher",)),
            evidence=evidence,
            raw_metadata={
                "source_category": str(context.settings.get("source_category") or "open_call_api"),
                "coverage_role": str(context.settings.get("coverage_role") or "primary"),
                "item_kind": "detail",
                "source_status": source_status,
                "call_identifier": _first_value(metadata, "callIdentifier"),
                "topic_identifier": identifier,
            },
        )


def _first_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    if isinstance(value, list | tuple):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value is not None else ""


def _status_label(status: str, sort_status: str = "") -> str:
    normalized = status.casefold().strip()
    if normalized in {"31094502", "open"} or sort_status == "1":
        return "open"
    if normalized in {"31094501", "forthcoming", "upcoming"} or sort_status == "2":
        return "upcoming"
    if normalized in {"31094503", "closed"} or sort_status == "3":
        return "closed"
    return normalized


def _json_list(value: str) -> list[dict[str, Any]]:
    parsed = _json_object_or_list(value)
    return parsed if isinstance(parsed, list) else []


def _json_object(value: str) -> dict[str, Any]:
    parsed = _json_object_or_list(value)
    return parsed if isinstance(parsed, dict) else {}


def _json_object_or_list(value: str) -> object:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _funding_text(
    *,
    metadata: dict[str, Any],
    action: dict[str, Any],
    budget: dict[str, Any],
    context: CrawlContext,
) -> str:
    action_types = _first_value(metadata, "typesOfAction")
    call_title = _first_value(metadata, "callTitle")
    status = cast(dict[str, Any], action.get("status")) if isinstance(action.get("status"), dict) else {}
    deadline_model = _first_value(metadata, "deadlineModel") or str(action.get("deadlineModel") or "")
    budget_text = _budget_excerpt(budget)
    parts = [
        str(context.settings.get("funding_scope") or "Horizon Europe calls and Türkiye guidance"),
        action_types,
        call_title,
        budget_text,
        str(status.get("description") or ""),
        deadline_model,
    ]
    return " | ".join(part for part in parts if part)


def _budget_excerpt(budget: dict[str, Any]) -> str:
    topic_map = budget.get("budgetTopicActionMap")
    if not isinstance(topic_map, dict):
        return ""
    for actions in topic_map.values():
        if not isinstance(actions, list):
            continue
        for action in actions:
            if not isinstance(action, dict):
                continue
            min_contribution = action.get("minContribution")
            max_contribution = action.get("maxContribution")
            expected_grants = action.get("expectedGrants")
            if min_contribution or max_contribution or expected_grants:
                return (
                    f"Indicative contribution {min_contribution or '?'}-{max_contribution or '?'} EUR; "
                    f"expected grants {expected_grants or '?'}"
                )
    return ""


def _eligibility_excerpt(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"Eligible countries(.{0,500})", text, flags=re.IGNORECASE | re.DOTALL)
    return _clean_html(match.group(0)) if match else text[:500].strip()


def _clean_html(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _first_non_empty(*values: str) -> str:
    return next((value.strip() for value in values if value and value.strip()), "")


def _tuple_setting(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _parse_utc_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    normalized = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", normalized)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _evidence(
    field_name: str,
    source_url: str,
    excerpt: str,
    selector_or_path: str,
    confidence: int,
) -> ParsedEvidence | None:
    if not excerpt.strip():
        return None
    return ParsedEvidence(
        field_name=field_name,
        source_url=source_url,
        source_excerpt=excerpt[:500],
        selector_or_path=selector_or_path,
        confidence=confidence,
    )
