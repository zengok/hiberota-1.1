from __future__ import annotations

from datetime import UTC, datetime

from django.test import SimpleTestCase

from automation.adapters.contracts import (
    CrawlContext,
    DiscoveredItem,
    FetchResult,
    ParsedCall,
    SourceAdapter,
)


class ExampleAdapter:
    key = "example_html_v1"
    parser_version = "2026-06-25"

    def discover(self, context: CrawlContext) -> list[DiscoveredItem]:
        return [
            DiscoveredItem(
                source_url=context.source_url,
                normalized_url=context.source_url,
                title_hint="Example call",
            )
        ]

    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        return FetchResult(
            item=item,
            final_url=item.normalized_url,
            status_code=200,
            content_type="text/html",
            body_text="<h1>Example call</h1>",
            fetched_at=datetime.now(UTC),
            content_hash="hash",
            evidence_excerpt="Example call",
        )

    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        return ParsedCall(
            title="Example call",
            official_url=result.final_url,
            canonical_source_url=result.final_url,
        )


class AdapterContractTests(SimpleTestCase):
    def test_example_adapter_satisfies_protocol(self) -> None:
        adapter = ExampleAdapter()

        self.assertIsInstance(adapter, SourceAdapter)

    def test_adapter_contract_round_trip(self) -> None:
        adapter = ExampleAdapter()
        context = CrawlContext(
            source_key="example",
            source_url="https://example.org/calls",
            adapter_key=adapter.key,
            config_version=1,
        )

        item = next(iter(adapter.discover(context)))
        result = adapter.fetch_detail(item, context)
        parsed = adapter.parse(result, context)

        self.assertEqual(parsed.title, "Example call")
        self.assertEqual(parsed.official_url, "https://example.org/calls")
