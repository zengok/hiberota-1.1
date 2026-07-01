from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from html import unescape
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

import defusedxml.ElementTree as ET

from automation.adapters.contracts import CrawlContext, DiscoveredItem, FetchResult, ParsedCall, ParsedEvidence


class JsonApiAdapter:
    key = "example_api_v1"
    parser_version = "2026-06-25"

    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        yield DiscoveredItem(source_url=context.source_url, normalized_url=context.source_url)

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        raise NotImplementedError("Controlled HTTP client supplies FetchResult in the pipeline.")

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        data = json.loads(result.body_text)
        return ParsedCall(
            title=str(data["title"]),
            official_url=str(data.get("official_url") or result.final_url),
            canonical_source_url=result.final_url,
            institution_name=str(data.get("institution_name", "")),
            summary=str(data.get("summary", "")),
            country_codes=tuple(data.get("country_codes", ())),
            audience_keys=tuple(data.get("audience_keys", ())),
        )


class AtomFeedAdapter:
    key = "example_feed_v1"
    parser_version = "2026-06-25"

    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        yield DiscoveredItem(source_url=context.source_url, normalized_url=context.source_url)

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        raise NotImplementedError("Controlled HTTP client supplies FetchResult in the pipeline.")

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        root = ET.fromstring(result.body_text)
        title = root.findtext(".//{http://www.w3.org/2005/Atom}title") or ""
        link = root.find(".//{http://www.w3.org/2005/Atom}link")
        href = (link.attrib.get("href") if link is not None else None) or result.final_url
        summary = root.findtext(".//{http://www.w3.org/2005/Atom}summary") or ""
        return ParsedCall(
            title=title,
            official_url=href,
            canonical_source_url=href,
            summary=summary,
        )


class StaticHtmlAdapter:
    key = "example_html_v1"
    parser_version = "2026-06-30"

    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        metadata = {"kind": "detail"} if context.settings.get("parse_listing_as_detail") else {}
        yield DiscoveredItem(source_url=context.source_url, normalized_url=context.source_url, metadata=metadata)

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        raise NotImplementedError("Controlled HTTP client supplies FetchResult in the pipeline.")

    def discover_from_fetch(self, result: FetchResult, context: CrawlContext) -> tuple[DiscoveredItem, ...]:
        if result.item.metadata.get("kind") == "detail":
            return ()

        max_links = int(context.settings.get("max_detail_links") or 20)
        structured_items = _extract_structured_call_rows(
            html=result.body_text,
            base_url=result.final_url,
            source_url=context.source_url,
        )
        if structured_items:
            return tuple(structured_items[:max_links])

        candidates = _extract_detail_links(
            html=result.body_text,
            base_url=result.final_url,
            source_url=context.source_url,
            keywords=tuple(context.settings.get("detail_link_keywords") or _DEFAULT_DETAIL_KEYWORDS),
            excluded_keywords=tuple(
                context.settings.get("excluded_detail_link_keywords") or _DEFAULT_EXCLUDED_DETAIL_KEYWORDS
            ),
        )
        return tuple(
            DiscoveredItem(
                source_url=result.final_url,
                normalized_url=url,
                title_hint=text,
                metadata={"kind": "detail", "listing_url": result.final_url},
            )
            for url, text in candidates[:max_links]
        )

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        source_status = _first_non_empty(
            str(result.item.metadata.get("source_status", "")),
            _extract_source_status(result.body_text, context.settings),
        )
        application_open_at = _first_non_empty_datetime(
            _parse_utc_date(result.item.metadata.get("application_open_at")),
            _parse_utc_date(context.settings.get("application_open_date_override")),
        )
        deadline_at = _first_non_empty_datetime(
            _parse_utc_date(result.item.metadata.get("deadline_at")),
            _parse_utc_date(context.settings.get("deadline_date_override")),
            _extract_deadline_at(result.body_text, context.settings),
        )
        title = _first_non_empty(
            str(context.settings.get("title_override", "")),
            str(result.item.title_hint or result.item.metadata.get("title_hint", "")),
            _extract_tag_text(result.body_text, "h1"),
            _extract_meta_content(result.body_text, "og:title"),
            _extract_tag_text(result.body_text, "title"),
        )
        summary = _first_non_empty(
            str(context.settings.get("summary_override", "")),
            _extract_meta_content(result.body_text, "description"),
            _extract_meta_content(result.body_text, "og:description"),
            str(result.item.metadata.get("summary_hint", "")),
            _extract_tag_text(result.body_text, "p"),
        )
        evidence = tuple(
            item
            for item in (
                _evidence("title", result.final_url, title, "h1|meta[property=og:title]|title", 80),
                _evidence("summary", result.final_url, summary, "meta[name=description]|p", 70),
                _evidence("source_status", result.final_url, source_status, "configured status regex|status field", 80),
                _evidence(
                    "application_open_at",
                    result.final_url,
                    application_open_at.isoformat() if application_open_at else "",
                    "listing metadata|configured open date",
                    80,
                ),
                _evidence(
                    "deadline",
                    result.final_url,
                    deadline_at.isoformat() if deadline_at else "",
                    "listing metadata|time[datetime]|configured deadline regex",
                    80,
                ),
            )
            if item is not None
        )
        return ParsedCall(
            title=title,
            official_url=result.final_url,
            canonical_source_url=result.final_url,
            institution_name=str(context.settings.get("institution_name_override", "")),
            summary=summary,
            eligibility_text=str(context.settings.get("eligibility_text_override", "")),
            funding_text=str(
                context.settings.get("funding_text_override") or context.settings.get("funding_scope", "")
            ),
            application_process_text=str(context.settings.get("application_process_text_override", "")),
            application_open_at=application_open_at,
            deadline_at=deadline_at,
            country_codes=_tuple_setting(context.settings.get("country_codes_override")),
            audience_keys=_tuple_setting(
                context.settings.get("audience_keys_override") or context.settings.get("audience_hints")
            ),
            evidence=evidence,
            raw_metadata={
                "source_category": str(context.settings.get("source_category", "")),
                "coverage_role": str(context.settings.get("coverage_role", "")),
                "item_kind": str(result.item.metadata.get("kind", "")),
                "source_status": source_status,
            },
        )


_DEFAULT_DETAIL_KEYWORDS = (
    # English
    "apply",
    "application",
    "call",
    "calls",
    "funding",
    "grant",
    "grants",
    "opportunit",
    "proposal",
    "proposals",
    # Turkish
    "basvur",
    "başvur",
    "cagri",
    "çağrı",
    "destek",
    "hibe",
    "fon",
    "proje",
    "duyuru",
    "ilan",
    "program",
    "burs",
)

_DEFAULT_EXCLUDED_DETAIL_KEYWORDS = (
    # English
    "about",
    "annual",
    "apply-for-funding",
    "application-process",
    "applying-funding",
    "contact",
    "eligibility",
    "faq",
    "filter_order=",
    "funding-stages",
    "grantee",
    "grantees",
    "guidance",
    "guideline",
    "funding/applying",
    "how-to-apply",
    "innovation-library",
    "library",
    "managing-funds",
    "manage-your-award",
    "monitoring",
    "news",
    "opportunities.html",
    "publication",
    "report",
    "story",
    "stories",
    "summary",
    "status=closed",
    "status=open",
    "status=upcoming",
    "why-applications-dont-always-succeed",
    "what-we-do",
    "what-we-offer",
    # Turkish — genel navigasyon linkleri hariç tut
    "hakkinda",
    "hakkimizda",
    "iletisim",
    "kurumsal",
    "mevzuat",
    "yayinlar",
    "haberler",
    "basin",
    "tarihce",
    "misyon",
    "vizyon",
    "sss",
    "sikca-sorulan",
    "kvkk",
    "gizlilik",
    "cerez",
    "dokuman",
    "doküman",
    "ihale",
    "kilavuz",
    "kılavuz",
    "satinalma",
    "satın alma",
    "sonuc",
    "sonuç",
    "sonuclari",
    "sonuçları",
    "tamamlandi",
    "tamamlandı",
)


def _extract_tag_text(html: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return _clean_html_text(match.group(1))


def _extract_meta_content(html: str, name_or_property: str) -> str:
    patterns = (
        rf'<meta[^>]+name=["\']{re.escape(name_or_property)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+property=["\']{re.escape(name_or_property)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name_or_property)}["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(name_or_property)}["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_html_text(match.group(1))
    return ""


_STATUS_LABELS = (
    # English
    "Opportunity status",
    "Status",
    "Call status",
    # Turkish
    "Çağrı Durumu",
    "Durum",
    "Başvuru Durumu",
    "İlan Durumu",
)


def _extract_source_status(html: str, settings: Any) -> str:
    configured_status = _first_regex_match(html, _tuple_setting(_setting_value(settings, "status_regex_patterns")))
    status_text = _first_non_empty(
        configured_status,
        _field_item_after_class(html, "field-award-status"),
        _field_text_after_label(html, _STATUS_LABELS),
    )
    normalized = status_text.casefold()
    page_text = _clean_html_text(html).casefold()
    closed_values = _tuple_setting(_setting_value(settings, "status_closed_values")) or ("closed", "kapalı")
    open_values = _tuple_setting(_setting_value(settings, "status_open_values")) or ("open", "açık")
    if any(value.casefold() in normalized for value in closed_values):
        return "closed"
    if any(value.casefold() in normalized for value in open_values):
        return "open"
    open_phrases = (
        "başvuruya açılmıştır",
        "başvuruya açıldı",
        "başvuruları başladı",
        "çağrısı açıldı",
        "çağrıları açıldı",
        "cagrisi acildi",
        "cagrilari acildi",
    )
    if any(phrase in page_text for phrase in open_phrases):
        return "open"
    return ""


_DEADLINE_LABELS = (
    # English
    "Closing date",
    "Deadline",
    "Application deadline",
    "Call deadline",
    "Submission deadline",
    # Turkish
    "Son Başvuru Tarihi",
    "Son Başvuru",
    "Başvuru Son Tarihi",
    "Son Tarih",
    "Bitiş Tarihi",
    "Çağrı Kapanış Tarihi",
    "Başvuru Tarihi",
    "Son Katılım Tarihi",
)


def _extract_deadline_at(html: str, settings: Any) -> datetime | None:
    configured_deadline = _first_regex_match(html, _tuple_setting(_setting_value(settings, "deadline_regex_patterns")))
    if configured_deadline:
        parsed_configured_deadline = _parse_utc_date(configured_deadline)
        if parsed_configured_deadline is not None:
            return parsed_configured_deadline
    deadline_value = _first_non_empty(
        _time_datetime_after_label(html, _DEADLINE_LABELS),
        _field_text_after_label(html, _DEADLINE_LABELS),
        _time_datetime_after_class(html, "field-award-deadline"),
    )
    return _parse_utc_date(deadline_value)


def _extract_structured_call_rows(*, html: str, base_url: str, source_url: str) -> list[DiscoveredItem]:
    allowed_host = urlparse(source_url).hostname
    items: list[DiscoveredItem] = []
    seen: set[str] = set()
    title_pattern = (
        r'<div[^>]+class=["\'][^"\']*\bc-baslik\b[^"\']*["\'][^>]*>.*?'
        r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    )
    for title_match in re.finditer(title_pattern, html, flags=re.IGNORECASE | re.DOTALL):
        row_start = html.rfind("views-row", 0, title_match.start())
        if row_start == -1:
            continue
        row_start = html.rfind("<div", 0, row_start)
        next_row = html.find("views-row", title_match.end())
        row_end = html.find("</main>", title_match.end())
        if row_end == -1:
            row_end = html.find("</body>", title_match.end())
        if next_row != -1:
            next_row_start = html.rfind("<div", 0, next_row)
            if next_row_start > title_match.end():
                row_end = next_row_start
        if row_end == -1:
            row_end = min(len(html), title_match.end() + 2400)
        row = html[row_start:row_end]
        normalized_url = urldefrag(urljoin(base_url, unescape(title_match.group(1)).strip())).url
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"https", "http"} or not _hosts_match(parsed.hostname or "", allowed_host or ""):
            continue
        if normalized_url.rstrip("/") == source_url.rstrip("/") or normalized_url in seen:
            continue
        times = re.findall(r'<time[^>]+datetime=["\']([^"\']+)["\']', row, flags=re.IGNORECASE | re.DOTALL)
        summary = _first_non_empty(_field_text_after_class(row, "c-icerik"), _clean_html_text(row))
        title = _clean_html_text(title_match.group(2))
        metadata = {
            "kind": "detail",
            "listing_url": base_url,
            "title_hint": title,
            "summary_hint": summary,
            "source_status": "open",
        }
        if times:
            metadata["application_open_at"] = times[0]
        if len(times) >= 2:
            metadata["deadline_at"] = times[1]
        seen.add(normalized_url)
        items.append(
            DiscoveredItem(
                source_url=base_url,
                normalized_url=normalized_url,
                title_hint=title,
                metadata=metadata,
            )
        )
    return items


def _field_text_after_label(html: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(
            rf"<dt[^>]*>\s*{re.escape(label)}\s*:?\s*</dt>\s*<dd[^>]*>(.*?)</dd>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return _clean_html_text(match.group(1))
    return ""


def _time_datetime_after_label(html: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(
            rf"<dt[^>]*>\s*{re.escape(label)}\s*:?\s*</dt>\s*<dd[^>]*>.*?<time[^>]+datetime=[\"']([^\"']+)[\"']",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1)
    return ""


def _field_item_after_class(html: str, class_fragment: str) -> str:
    marker_match = re.search(rf'<[^>]+class=["\'][^"\']*{re.escape(class_fragment)}[^"\']*["\']', html, re.IGNORECASE)
    if not marker_match:
        return ""
    snippet = html[marker_match.start() : marker_match.start() + 1200]
    item_match = re.search(
        r'<div[^>]+class=["\'][^"\']*field__item[^"\']*["\'][^>]*>(.*?)</div>',
        snippet,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not item_match:
        return ""
    return _clean_html_text(item_match.group(1))


def _field_text_after_class(html: str, class_fragment: str) -> str:
    marker_match = re.search(rf'<[^>]+class=["\'][^"\']*{re.escape(class_fragment)}[^"\']*["\']', html, re.IGNORECASE)
    if not marker_match:
        return ""
    snippet = html[marker_match.start() : marker_match.start() + 1200]
    block_match = re.search(r"<div[^>]*>(.*?)</div>", snippet, flags=re.IGNORECASE | re.DOTALL)
    if not block_match:
        return ""
    return _clean_html_text(block_match.group(1))


def _time_datetime_after_class(html: str, class_fragment: str) -> str:
    marker_match = re.search(rf'<[^>]+class=["\'][^"\']*{re.escape(class_fragment)}[^"\']*["\']', html, re.IGNORECASE)
    if not marker_match:
        return ""
    snippet = html[marker_match.start() : marker_match.start() + 1600]
    time_match = re.search(r'<time[^>]+datetime=["\']([^"\']+)["\']', snippet, flags=re.IGNORECASE | re.DOTALL)
    return time_match.group(1) if time_match else ""


def _first_regex_match(text: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_html_text(match.group(1) if match.groups() else match.group(0))
    return ""


def _extract_detail_links(
    *,
    html: str,
    base_url: str,
    source_url: str,
    keywords: tuple[str, ...],
    excluded_keywords: tuple[str, ...],
) -> list[tuple[str, str]]:
    allowed_host = urlparse(source_url).hostname
    seen: set[str] = set()
    links: list[tuple[str, str]] = []
    for href, text in re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        normalized_url = urldefrag(urljoin(base_url, unescape(href).strip())).url
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"https", "http"} or not _hosts_match(parsed.hostname or "", allowed_host or ""):
            continue
        if normalized_url.rstrip("/") == source_url.rstrip("/") or normalized_url in seen:
            continue
        label = _clean_html_text(text)
        haystack = f"{parsed.path} {parsed.query} {label}".casefold()
        if any(keyword.casefold() in haystack for keyword in excluded_keywords):
            continue
        if not any(keyword.casefold() in haystack for keyword in keywords):
            continue
        seen.add(normalized_url)
        links.append((normalized_url, label))
    return links


def _clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", value))).strip()


def _hosts_match(candidate_host: str, allowed_host: str) -> bool:
    candidate = candidate_host.casefold().removeprefix("www.")
    allowed = allowed_host.casefold().removeprefix("www.")
    return bool(candidate and allowed and candidate == allowed)


def _first_non_empty(*values: str) -> str:
    return next((value.strip() for value in values if value.strip()), "")


def _tuple_setting(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _setting_value(settings: Any, key: str) -> Any:
    return settings.get(key) if hasattr(settings, "get") else None


def _parse_utc_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
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


def _first_non_empty_datetime(*values: datetime | None) -> datetime | None:
    return next((value for value in values if value is not None), None)


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
