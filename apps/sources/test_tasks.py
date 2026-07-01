from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

from automation.http.client import SafeHttpResponse
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings

from apps.calls.models import GrantCall
from apps.ingestion.models import CrawlItem, CrawlRun
from apps.institutions.models import Country, Institution
from apps.sources.models import Source
from apps.sources.tasks import _safe_http_request_for, crawl_source
from apps.taxonomy.models import AudienceType

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "automation" / "adapters" / "fixtures"


class SourceCrawlTaskTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")
        self.source = Source.objects.create(
            institution=self.institution,
            source_key="source-a",
            name="Kaynak A",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="source-a_html_v1",
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_crawl_source_fetches_parses_and_persists_call(self, fetch_url: Mock) -> None:
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/calls",
            status_code=200,
            content_type="text/html",
            body=b"<html><body><h1>Yeni Hibe Programi</h1><p>Program ozeti</p></body></html>",
            headers={"content-type": "text/html"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:1")
        self.assertEqual(GrantCall.objects.count(), 1)
        call = GrantCall.objects.get()
        self.assertEqual(call.title, "Yeni Hibe Programi")
        self.assertEqual(call.summary, "Program ozeti")
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        run = CrawlRun.objects.get()
        item = CrawlItem.objects.get()
        self.assertEqual(run.status, CrawlRun.Status.COMPLETED)
        self.assertEqual(run.discovered_count, 1)
        self.assertEqual(run.fetched_count, 1)
        self.assertEqual(run.created_count, 1)
        self.assertEqual(run.review_count, 1)
        self.assertEqual(run.http_status_summary, {"200": 1})
        self.assertEqual(item.status, CrawlItem.Status.PARSED)
        self.assertEqual(item.grant_call, call)
        self.source.refresh_from_db()
        self.assertIsNotNone(self.source.last_success_at)
        self.assertEqual(self.source.consecutive_failures, 0)

    @patch("apps.sources.tasks.fetch_url_with_retries", side_effect=RuntimeError("network failed"))
    def test_crawl_source_records_item_failure_and_continues(self, fetch_url: Mock) -> None:
        # Item-level failures are caught and logged; the run completes so other items can be processed.
        result = crawl_source(self.source.id)

        fetch_url.assert_called_once()
        self.assertEqual(result, "persisted:0")
        self.source.refresh_from_db()
        self.assertIsNone(self.source.last_success_at)
        self.assertIsNotNone(self.source.last_failure_at)
        self.assertEqual(self.source.consecutive_failures, 1)
        self.assertEqual(GrantCall.objects.count(), 0)
        run = CrawlRun.objects.get()
        item = CrawlItem.objects.get()
        self.assertEqual(run.status, CrawlRun.Status.COMPLETED)
        self.assertEqual(run.failed_count, 1)
        self.assertEqual(run.error_code, "")
        self.assertEqual(item.status, CrawlItem.Status.FAILED)

    @override_settings(SOURCE_SCHEDULER_DEGRADE_AFTER_FAILURES=3)
    @patch("apps.sources.tasks.fetch_url_with_retries", side_effect=RuntimeError("network failed"))
    def test_crawl_source_degrades_source_after_failure_threshold(self, fetch_url: Mock) -> None:
        self.source.consecutive_failures = 2
        self.source.save(update_fields=["consecutive_failures", "updated_at"])

        result = crawl_source(self.source.id)

        fetch_url.assert_called_once()
        self.assertEqual(result, "persisted:0")
        self.source.refresh_from_db()
        self.assertEqual(self.source.consecutive_failures, 3)
        self.assertEqual(self.source.status, Source.Status.DEGRADED)

    def test_safe_http_request_uses_source_config_and_host_allowlist(self) -> None:
        self.source.config_json = {
            "robots_txt": "User-agent: *\nDisallow: /private\n",
            "user_agent": "HibeRotaBot/Test",
            "timeout_seconds": 4,
            "max_redirects": 1,
            "max_response_bytes": 12345,
            "min_request_interval_seconds": 2,
            "allowed_detail_hosts": ["api.example.org"],
        }
        self.source.save(update_fields=["config_json", "updated_at"])

        request = _safe_http_request_for(source=self.source, url="https://example.org/calls")

        self.assertEqual(
            request.allowed_hosts,
            frozenset({"api.example.org", "example.org", "www.api.example.org", "www.example.org"}),
        )
        self.assertEqual(request.robots_txt, "User-agent: *\nDisallow: /private\n")
        self.assertEqual(request.user_agent, "HibeRotaBot/Test")
        self.assertEqual(request.timeout_seconds, 4)
        self.assertEqual(request.max_redirects, 1)
        self.assertEqual(request.max_response_bytes, 12345)
        self.assertEqual(request.min_request_interval_seconds, 2)

    def test_safe_http_request_builds_multipart_post_from_source_config(self) -> None:
        self.source.config_json = {
            "http_method": "POST",
            "multipart_json_parts": {
                "query": {"bool": {"must": [{"term": {"programmePeriod": "2021 - 2027"}}]}},
                "languages": ["en"],
            },
        }
        self.source.save(update_fields=["config_json", "updated_at"])

        request = _safe_http_request_for(source=self.source, url="https://example.org/search")

        self.assertEqual(request.method, "POST")
        self.assertIsNotNone(request.body)
        self.assertIn("multipart/form-data; boundary=", request.extra_headers["Content-Type"])
        body = (request.body or b"").decode()
        self.assertIn('name="query"; filename="blob"', body)
        self.assertIn('"programmePeriod": "2021 - 2027"', body)
        self.assertIn('name="languages"; filename="blob"', body)

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_crawl_source_passes_safe_http_request_to_retrying_client(self, fetch_url: Mock) -> None:
        self.source.config_json = {"max_response_bytes": 2048, "robots_txt": "User-agent: *\nAllow: /\n"}
        self.source.save(update_fields=["config_json", "updated_at"])
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/calls",
            status_code=200,
            content_type="text/html",
            body=b"<html><body><h1>Yeni Hibe Programi</h1><p>Program ozeti</p></body></html>",
            headers={"content-type": "text/html"},
        )

        crawl_source(self.source.id)

        request = fetch_url.call_args.args[0]
        self.assertEqual(request.allowed_hosts, frozenset({"example.org", "www.example.org"}))
        self.assertEqual(request.max_response_bytes, 2048)
        self.assertEqual(request.robots_txt, "User-agent: *\nAllow: /\n")

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_static_html_fixture_crawls_parses_and_persists_end_to_end(self, fetch_url: Mock) -> None:
        fixture_body = (FIXTURES_DIR / "static_html" / "call_detail.html").read_bytes()
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/calls/static-fixture",
            status_code=200,
            content_type="text/html",
            body=fixture_body,
            headers={"content-type": "text/html"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:1")
        call = GrantCall.objects.get()
        self.assertEqual(call.title, "Yerel Kalkinma Destek Programi")
        self.assertEqual(call.summary, "KOBI ve kooperatiflerin kapasite gelistirme projeleri desteklenir.")
        self.assertEqual(call.source, self.source)
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.REVIEW)
        run = CrawlRun.objects.get()
        item = CrawlItem.objects.get()
        self.assertEqual(run.status, CrawlRun.Status.COMPLETED)
        self.assertEqual(run.created_count, 1)
        self.assertEqual(run.review_count, 1)
        self.assertEqual(item.status, CrawlItem.Status.PARSED)
        self.assertEqual(item.parser_version, "2026-06-30")

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_html_listing_discovers_detail_links_before_persisting_calls(self, fetch_url: Mock) -> None:
        self.source.config_json = {"source_category": "programme_portal", "max_detail_links": 2}
        self.source.save(update_fields=["config_json", "updated_at"])
        fetch_url.side_effect = [
            SafeHttpResponse(
                final_url="https://example.org/calls",
                status_code=200,
                content_type="text/html",
                body=b"""
                <html><body>
                  <a href="/calls/open-grant-1">Open grant application</a>
                  <a href="https://other.example/calls/open-grant-2">External grant</a>
                </body></html>
                """,
                headers={"content-type": "text/html"},
            ),
            SafeHttpResponse(
                final_url="https://example.org/calls/open-grant-1",
                status_code=200,
                content_type="text/html",
                body=b"<html><body><h1>Open Grant Application</h1><p>Detail summary</p></body></html>",
                headers={"content-type": "text/html"},
            ),
        ]

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:1")
        self.assertEqual(fetch_url.call_count, 2)
        self.assertEqual(GrantCall.objects.count(), 1)
        call = GrantCall.objects.get()
        self.assertEqual(call.title, "Open Grant Application")
        self.assertEqual(call.canonical_source_url, "https://example.org/calls/open-grant-1")
        self.assertEqual(CrawlItem.objects.count(), 2)
        listing_item, detail_item = CrawlItem.objects.order_by("id")
        self.assertEqual(listing_item.status, CrawlItem.Status.FETCHED)
        self.assertEqual(listing_item.raw_metadata_json["detail_count"], 1)
        self.assertEqual(detail_item.status, CrawlItem.Status.PARSED)
        run = CrawlRun.objects.get()
        self.assertEqual(run.discovered_count, 2)
        self.assertEqual(run.fetched_count, 2)
        self.assertEqual(run.created_count, 1)

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_portal_listing_without_detail_links_does_not_persist_call(self, fetch_url: Mock) -> None:
        self.source.config_json = {"source_category": "programme_portal"}
        self.source.save(update_fields=["config_json", "updated_at"])
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/calls",
            status_code=200,
            content_type="text/html",
            body=b"""
            <html><body>
              <h1>Small Grants Programme</h1>
              <a href="/about-us-157/our-grantees.html">Our grantees</a>
              <a href="/about-us-157/how-to-apply.html">How to apply</a>
              <a href="/about-us-157/grant-eligibility.html">Grant eligibility</a>
              <a href="/about-us-157/opportunities.html">Opportunities</a>
            </body></html>
            """,
            headers={"content-type": "text/html"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:0")
        self.assertEqual(GrantCall.objects.count(), 0)
        item = CrawlItem.objects.get()
        self.assertEqual(item.status, CrawlItem.Status.FETCHED)
        self.assertEqual(item.raw_metadata_json["detail_count"], 0)
        self.assertEqual(item.raw_metadata_json["skipped_reason"], "no_detail_links")
        run = CrawlRun.objects.get()
        self.assertEqual(run.discovered_count, 1)
        self.assertEqual(run.fetched_count, 1)
        self.assertEqual(run.created_count, 0)
        self.assertEqual(run.review_count, 0)

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_central_portal_listing_without_detail_links_does_not_persist_call(self, fetch_url: Mock) -> None:
        self.source.config_json = {"source_category": "central_portal"}
        self.source.save(update_fields=["config_json", "updated_at"])
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/funding",
            status_code=200,
            content_type="text/html",
            body=b"<html><body><h1>Funding portal</h1><p>General funding information</p></body></html>",
            headers={"content-type": "text/html"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:0")
        self.assertEqual(GrantCall.objects.count(), 0)
        item = CrawlItem.objects.get()
        self.assertEqual(item.raw_metadata_json["skipped_reason"], "no_detail_links")

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_direct_call_listing_config_persists_as_detail_item(self, fetch_url: Mock) -> None:
        self.source.config_json = {"source_category": "programme_portal", "parse_listing_as_detail": True}
        self.source.save(update_fields=["config_json", "updated_at"])
        fetch_url.return_value = SafeHttpResponse(
            final_url="https://example.org/call-for-project-proposals",
            status_code=200,
            content_type="text/html",
            body=b"<html><body><h1>Call for Project Proposals</h1><p>Official direct call page</p></body></html>",
            headers={"content-type": "text/html"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:1")
        call = GrantCall.objects.get()
        self.assertEqual(call.title, "Call for Project Proposals")
        item = CrawlItem.objects.get()
        self.assertEqual(item.status, CrawlItem.Status.PARSED)
        self.assertEqual(item.raw_metadata_json["kind"], "detail")

    @patch("apps.sources.tasks.fetch_url_with_retries")
    def test_metadata_only_detail_item_does_not_fetch_detail_url(self, fetch_url: Mock) -> None:
        AudienceType.objects.create(key="researcher", name_tr="Araştırmacı", name_en="Researcher")
        self.source.name = "Ufuk Avrupa Açık Horizon Europe Çağrıları"
        self.source.listing_url = "https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA"
        self.source.source_type = Source.SourceType.API
        self.source.adapter_key = "src-0022_eu_funding_v1"
        self.source.config_json = {
            "audience_hints": ["researcher"],
            "country_codes_override": ["TR"],
            "funding_scope": "Horizon Europe calls and Türkiye guidance",
            "http_method": "POST",
            "multipart_json_parts": {"query": {"bool": {"must": []}}, "languages": ["en"]},
            "source_category": "open_call_api",
        }
        self.source.save(
            update_fields=["name", "listing_url", "source_type", "adapter_key", "config_json", "updated_at"]
        )
        fetch_url.return_value = SafeHttpResponse(
            final_url=self.source.listing_url,
            status_code=200,
            content_type="application/json",
            body=json.dumps({"results": [self.eu_funding_entry()]}).encode(),
            headers={"content-type": "application/json"},
        )

        result = crawl_source(self.source.id)

        self.assertEqual(result, "persisted:1")
        fetch_url.assert_called_once()
        call = GrantCall.objects.get()
        self.assertEqual(call.workflow_status, GrantCall.WorkflowStatus.PUBLISHED)
        self.assertEqual(call.availability_status, GrantCall.AvailabilityStatus.OPEN)
        self.assertEqual(call.external_id, "HORIZON-TEST-OPEN")
        self.assertEqual(call.audiences.get().key, "researcher")
        listing_item, detail_item = CrawlItem.objects.order_by("id")
        self.assertEqual(listing_item.raw_metadata_json["detail_count"], 1)
        self.assertEqual(detail_item.status, CrawlItem.Status.PARSED)
        self.assertTrue(detail_item.raw_metadata_json["parse_without_fetch"])

    def eu_funding_entry(self) -> dict[str, object]:
        return {
            "reference": "HORIZON-TEST-OPENTOPICSen",
            "summary": "Open Horizon topic",
            "url": (
                "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/"
                "topic-details/HORIZON-TEST-OPEN"
            ),
            "metadata": {
                "identifier": ["HORIZON-TEST-OPEN"],
                "title": ["Open Horizon topic"],
                "url": [
                    "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/"
                    "topic-details/HORIZON-TEST-OPEN"
                ],
                "status": ["31094502"],
                "sortStatus": ["1"],
                "startDate": ["2026-05-05T00:00:00.000+0000"],
                "deadlineDate": ["2026-09-15T00:00:00.000+0000"],
                "callTitle": ["Clean Energy Test Call"],
                "typesOfAction": ["HORIZON Research and Innovation Actions"],
                "descriptionByte": ["<p>Expected Outcome:</p><p>Reliable public topic summary.</p>"],
                "topicConditions": [
                    "<h4>Eligible countries</h4><p>Eligible countries are described in Annex B.</p>"
                ],
                "actions": [
                    json.dumps(
                        [
                            {
                                "status": {"id": 31094502, "description": "Open"},
                                "plannedOpeningDate": "2026-05-05",
                                "deadlineDates": ["2026-09-15"],
                            }
                        ]
                    )
                ],
                "budgetOverview": [
                    json.dumps(
                        {
                            "budgetTopicActionMap": {
                                "1": [
                                    {
                                        "minContribution": 1000000,
                                        "maxContribution": 2000000,
                                        "expectedGrants": 3,
                                    }
                                ]
                            }
                        }
                    )
                ],
            },
        }
