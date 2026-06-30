from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from django.test import SimpleTestCase

from automation.adapters.contracts import CrawlContext, DiscoveredItem, FetchResult
from automation.adapters.examples import AtomFeedAdapter, JsonApiAdapter, StaticHtmlAdapter

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "static_html"


class ExampleAdapterFixtureTests(SimpleTestCase):
    def setUp(self) -> None:
        self.context = CrawlContext(
            source_key="example",
            source_url="https://example.org/calls",
            adapter_key="example",
            config_version=1,
        )
        self.item = DiscoveredItem(
            source_url="https://example.org/calls/1",
            normalized_url="https://example.org/calls/1",
        )

    def result(self, body_text: str, content_type: str) -> FetchResult:
        return FetchResult(
            item=self.item,
            final_url=self.item.normalized_url,
            status_code=200,
            content_type=content_type,
            body_text=body_text,
            fetched_at=datetime(2026, 6, 25, tzinfo=UTC),
            content_hash="hash",
        )

    def fixture_result(self, fixture_name: str, final_url: str, source_url: str | None = None) -> FetchResult:
        item = DiscoveredItem(
            source_url=source_url or final_url,
            normalized_url=final_url,
        )
        return FetchResult(
            item=item,
            final_url=final_url,
            status_code=200,
            content_type="text/html",
            body_text=(FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"),
            fetched_at=datetime(2026, 6, 30, tzinfo=UTC),
            content_hash="hash",
        )

    def test_json_api_adapter_parses_fixture(self) -> None:
        parsed = JsonApiAdapter().parse(
            self.result(
                '{"title":"API çağrısı","institution_name":"Kurum","summary":"Özet","country_codes":["TR"]}',
                "application/json",
            ),
            self.context,
        )

        self.assertEqual(parsed.title, "API çağrısı")
        self.assertEqual(parsed.country_codes, ("TR",))

    def test_atom_feed_adapter_parses_fixture(self) -> None:
        parsed = AtomFeedAdapter().parse(
            self.result(
                """
                <feed xmlns="http://www.w3.org/2005/Atom">
                  <entry>
                    <title>Feed çağrısı</title>
                    <link href="https://example.org/feed-call" />
                    <summary>Feed özeti</summary>
                  </entry>
                </feed>
                """,
                "application/atom+xml",
            ),
            self.context,
        )

        self.assertEqual(parsed.title, "Feed çağrısı")
        self.assertEqual(parsed.official_url, "https://example.org/feed-call")

    def test_static_html_adapter_parses_fixture(self) -> None:
        parsed = StaticHtmlAdapter().parse(
            self.result("<html><body><h1>HTML çağrısı</h1><p>HTML özeti</p></body></html>", "text/html"),
            self.context,
        )

        self.assertEqual(parsed.title, "HTML çağrısı")
        self.assertEqual(parsed.summary, "HTML özeti")
        self.assertEqual(parsed.evidence[0].field_name, "title")

    def test_static_html_adapter_falls_back_to_title_and_meta_description(self) -> None:
        parsed = StaticHtmlAdapter().parse(
            self.result(
                """
                <html>
                  <head>
                    <title>Funding window | Official source</title>
                    <meta name="description" content="Official funding summary">
                  </head>
                  <body><main>No h1 here</main></body>
                </html>
                """,
                "text/html",
            ),
            self.context,
        )

        self.assertEqual(parsed.title, "Funding window | Official source")
        self.assertEqual(parsed.summary, "Official funding summary")
        self.assertEqual(parsed.evidence[1].field_name, "summary")

    def test_static_html_adapter_discovers_same_host_detail_links_from_listing(self) -> None:
        result = self.result(
            """
            <html><body>
              <a href="/funding/open-call-1">Open call for proposals</a>
              <a href="https://evil.example/grants">External grant</a>
              <a href="/about">About us</a>
              <a href="/about-us/how-to-apply.html">How to apply</a>
              <a href="/innovation-library/report.html">Annual grant report</a>
            </body></html>
            """,
            "text/html",
        )

        items = StaticHtmlAdapter().discover_from_fetch(result, self.context)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].normalized_url, "https://example.org/funding/open-call-1")
        self.assertEqual(items[0].metadata["kind"], "detail")

    def test_static_html_adapter_filters_generic_portal_information_links(self) -> None:
        result = self.result(
            """
            <html><body>
              <a href="/about-us-157/our-grantees.html">Our grantees</a>
              <a href="/about-us-157/how-to-apply.html">How to apply</a>
              <a href="/about-us-157/grant-eligibility.html">Grant eligibility</a>
              <a href="/about-us-157/opportunities.html">Opportunities</a>
              <a href="/innovation-library/item/2660-annual-monitoring-report.html">Annual monitoring report</a>
            </body></html>
            """,
            "text/html",
        )

        items = StaticHtmlAdapter().discover_from_fetch(result, self.context)

        self.assertEqual(items, ())

    def test_static_html_adapter_filters_known_guidance_links_but_keeps_funding_pages(self) -> None:
        result = self.result(
            """
            <html><body>
              <a href="/funding/applying-funding">Applying for funding</a>
              <a href="/funding/applying">Applying for funding</a>
              <a href="/funding/managing-funds">Managing funds</a>
              <a href="/funding/2026-international-joint-initiative-research">2026 International Joint Initiative</a>
              <a href="/funding/science-granting-councils-call-proposals">SGCI call for proposals</a>
              <a href="/funding-stages">Funding Stages</a>
              <a href="/application-process">Application Process</a>
              <a href="/why-applications-dont-always-succeed">Why applications don't always succeed</a>
              <a href="/applying-to-the-innovating-for-climate-resilience-fund">
                Applying to the Innovating for Climate Resilience Fund
              </a>
            </body></html>
            """,
            "text/html",
        )

        items = StaticHtmlAdapter().discover_from_fetch(result, self.context)

        self.assertEqual(
            [item.normalized_url for item in items],
            [
                "https://example.org/funding/2026-international-joint-initiative-research",
                "https://example.org/funding/science-granting-councils-call-proposals",
                "https://example.org/applying-to-the-innovating-for-climate-resilience-fund",
            ],
        )

    def test_static_html_adapter_can_treat_listing_url_as_detail_item(self) -> None:
        context = CrawlContext(
            source_key="direct-call",
            source_url="https://example.org/call-for-project-proposals",
            adapter_key="example",
            config_version=1,
            settings={"parse_listing_as_detail": True},
        )

        item = next(iter(StaticHtmlAdapter().discover(context)))

        self.assertEqual(item.normalized_url, "https://example.org/call-for-project-proposals")
        self.assertEqual(item.metadata["kind"], "detail")

    def test_static_html_adapter_uses_configured_title_and_summary_overrides(self) -> None:
        context = CrawlContext(
            source_key="direct-call",
            source_url="https://example.org/call",
            adapter_key="example",
            config_version=1,
            settings={
                "title_override": "UNDEF Call for Project Proposals",
                "summary_override": "Official UNDEF proposal call page.",
            },
        )

        parsed = StaticHtmlAdapter().parse(
            self.result(
                "<html><body><h1>Proposal Guideline</h1><p>Download documents below.</p></body></html>", "text/html"
            ),
            context,
        )

        self.assertEqual(parsed.title, "UNDEF Call for Project Proposals")
        self.assertEqual(parsed.summary, "Official UNDEF proposal call page.")

    def test_static_html_adapter_uses_configured_structured_field_overrides(self) -> None:
        context = CrawlContext(
            source_key="direct-call",
            source_url="https://example.org/call",
            adapter_key="example",
            config_version=1,
            settings={
                "institution_name_override": "United Nations Democracy Fund",
                "funding_scope": "Democracy; civil society; human rights",
                "eligibility_text_override": "Civil society organizations and NGOs.",
                "application_process_text_override": "Apply using the official proposal form.",
                "deadline_date_override": "2026-12-31",
                "country_codes_override": ["XX"],
                "audience_hints": ["ngo"],
            },
        )

        parsed = StaticHtmlAdapter().parse(
            self.result("<html><body><h1>Call</h1><p>Summary</p></body></html>", "text/html"),
            context,
        )

        self.assertEqual(parsed.institution_name, "United Nations Democracy Fund")
        self.assertEqual(parsed.funding_text, "Democracy; civil society; human rights")
        self.assertEqual(parsed.eligibility_text, "Civil society organizations and NGOs.")
        self.assertEqual(parsed.application_process_text, "Apply using the official proposal form.")
        self.assertEqual(parsed.deadline_at, datetime(2026, 12, 31, tzinfo=UTC))
        self.assertEqual(parsed.country_codes, ("XX",))
        self.assertEqual(parsed.audience_keys, ("ngo",))

    def test_static_html_adapter_extracts_default_status_and_deadline_fields(self) -> None:
        parsed = StaticHtmlAdapter().parse(
            self.result(
                """
                <html><body>
                  <h1>Call for proposals</h1>
                  <div class="field field--name-field-award-status field--type-list-string">
                    <div class="field__item">Closed</div>
                  </div>
                  <div class="field field--name-field-award-deadline field--type-datetime">
                    <div class="field__label">Deadline</div>
                    <div class="field__item">
                      <time datetime="2025-09-18T03:59:00Z">Wednesday, September 17, 2025 - 23:59 ET</time>
                    </div>
                  </div>
                </body></html>
                """,
                "text/html",
            ),
            self.context,
        )

        self.assertEqual(parsed.raw_metadata["source_status"], "closed")
        self.assertEqual(parsed.deadline_at, datetime(2025, 9, 18, 3, 59, tzinfo=UTC))
        self.assertIn("source_status", {evidence.field_name for evidence in parsed.evidence})
        self.assertIn("deadline", {evidence.field_name for evidence in parsed.evidence})

    def test_static_html_adapter_extracts_configured_status_and_deadline_patterns(self) -> None:
        context = CrawlContext(
            source_key="configured",
            source_url="https://example.org/call",
            adapter_key="example",
            config_version=1,
            settings={
                "status_regex_patterns": [r"Status:\s*(Open)"],
                "deadline_regex_patterns": [r"Deadline:\s*(2026-03-01)"],
            },
        )

        parsed = StaticHtmlAdapter().parse(
            self.result(
                "<html><body><h1>Call</h1><p>Status: Open</p><p>Deadline: 2026-03-01</p></body></html>",
                "text/html",
            ),
            context,
        )

        self.assertEqual(parsed.raw_metadata["source_status"], "open")
        self.assertEqual(parsed.deadline_at, datetime(2026, 3, 1, tzinfo=UTC))

    def test_static_html_adapter_ignores_invalid_deadline_override(self) -> None:
        context = CrawlContext(
            source_key="direct-call",
            source_url="https://example.org/call",
            adapter_key="example",
            config_version=1,
            settings={"deadline_date_override": "not-a-date"},
        )

        parsed = StaticHtmlAdapter().parse(
            self.result("<html><body><h1>Call</h1><p>Summary</p></body></html>", "text/html"),
            context,
        )

        self.assertIsNone(parsed.deadline_at)

    def test_static_html_adapter_discovers_eureka_www_open_call_fixture_links(self) -> None:
        context = CrawlContext(
            source_key="src-0085",
            source_url="https://eurekanetwork.org/opencalls/",
            adapter_key="src-0085_html_v1",
            config_version=1,
            settings={"max_detail_links": 5},
        )
        result = self.fixture_result(
            "eureka_open_calls_listing.html",
            "https://www.eurekanetwork.org/programmes-and-calls/",
            source_url="https://eurekanetwork.org/opencalls/",
        )

        items = StaticHtmlAdapter().discover_from_fetch(result, context)

        self.assertEqual(
            [item.normalized_url for item in items],
            [
                "https://www.eurekanetwork.org/programmes-and-calls/eurostars/",
                "https://www.eurekanetwork.org/programmes-and-calls/globalstars/",
            ],
        )
        self.assertNotIn("?status=open", {item.normalized_url for item in items})

    def test_static_html_adapter_parses_eureka_status_and_deadline_fixture(self) -> None:
        context = CrawlContext(
            source_key="src-0085",
            source_url="https://eurekanetwork.org/opencalls/",
            adapter_key="src-0085_html_v1",
            config_version=1,
            settings={"audience_hints": ["sme"], "funding_scope": "International industrial R&D and innovation"},
        )

        parsed = StaticHtmlAdapter().parse(
            self.fixture_result(
                "eureka_open_call_detail.html",
                "https://www.eurekanetwork.org/programmes-and-calls/eurostars/",
            ),
            context,
        )

        self.assertEqual(parsed.title, "Eurostars call")
        self.assertEqual(parsed.raw_metadata["source_status"], "open")
        self.assertEqual(parsed.deadline_at, datetime(2026, 9, 4, 12, 0, tzinfo=UTC))
        self.assertEqual(parsed.audience_keys, ("sme",))
        self.assertIn("deadline", {evidence.field_name for evidence in parsed.evidence})

    def test_static_html_adapter_discovers_ukri_opportunity_fixture_links(self) -> None:
        context = CrawlContext(
            source_key="src-0120",
            source_url="https://www.ukri.org/opportunity/",
            adapter_key="src-0120_html_v1",
            config_version=1,
            settings={"max_detail_links": 5},
        )
        result = self.fixture_result("ukri_opportunity_listing.html", "https://www.ukri.org/opportunity/")

        items = StaticHtmlAdapter().discover_from_fetch(result, context)

        self.assertEqual(
            [item.normalized_url for item in items],
            [
                "https://www.ukri.org/opportunity/2445-drive35-scale-up-fund/",
                "https://www.ukri.org/opportunity/next-wave-breakthrough-wave-1/",
            ],
        )

    def test_static_html_adapter_parses_ukri_label_value_status_and_deadline_fixture(self) -> None:
        context = CrawlContext(
            source_key="src-0120",
            source_url="https://www.ukri.org/opportunity/",
            adapter_key="src-0120_html_v1",
            config_version=1,
            settings={"audience_hints": ["researcher", "sme"], "funding_scope": "Research; innovation"},
        )

        parsed = StaticHtmlAdapter().parse(
            self.fixture_result(
                "ukri_opportunity_detail.html",
                "https://www.ukri.org/opportunity/2445-drive35-scale-up-fund/",
            ),
            context,
        )

        self.assertEqual(parsed.title, "Funding opportunity: 2445: DRIVE35: Scale Up Fund")
        self.assertEqual(parsed.summary, "Apply for grant funding to scale up innovation in advanced manufacturing.")
        self.assertEqual(parsed.raw_metadata["source_status"], "open")
        self.assertEqual(parsed.deadline_at, datetime(2026, 8, 15, 11, 0, tzinfo=UTC))
        self.assertEqual(parsed.audience_keys, ("researcher", "sme"))
        self.assertIn("source_status", {evidence.field_name for evidence in parsed.evidence})
