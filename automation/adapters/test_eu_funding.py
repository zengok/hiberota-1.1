from __future__ import annotations

import json
from datetime import UTC, datetime

from django.test import SimpleTestCase

from automation.adapters.contracts import CrawlContext, DiscoveredItem, FetchResult
from automation.adapters.eu_funding import EuFundingTendersAdapter
from automation.pipeline.confidence import calculate_confidence


class EuFundingTendersAdapterTests(SimpleTestCase):
    def setUp(self) -> None:
        self.context = CrawlContext(
            source_key="src-0022",
            source_url="https://api.tech.ec.europa.eu/search-api/prod/rest/search?apiKey=SEDIA",
            adapter_key="src-0022_eu_funding_v1",
            config_version=1,
            settings={
                "audience_hints": ["researcher"],
                "country_codes_override": ["EU", "TR"],
                "funding_scope": "Horizon Europe calls and Türkiye guidance",
                "max_detail_links": 10,
                "source_category": "open_call_api",
            },
        )

    def test_discovers_open_topic_records_from_search_api_response(self) -> None:
        result = self.result(self.api_response())

        items = EuFundingTendersAdapter().discover_from_fetch(result, self.context)

        self.assertEqual(len(items), 2)
        self.assertEqual(
            items[0].normalized_url,
            "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/HORIZON-TEST-OPEN",
        )
        self.assertEqual(items[0].metadata["source_status"], "open")
        self.assertEqual(items[1].metadata["source_status"], "upcoming")

    def test_parse_uses_api_metadata_for_publishable_call(self) -> None:
        adapter = EuFundingTendersAdapter()
        item = adapter.discover_from_fetch(self.result(self.api_response()), self.context)[0]
        detail_result = FetchResult(
            item=item,
            final_url=item.normalized_url,
            status_code=200,
            content_type="text/html",
            body_text="<html></html>",
            fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
            content_hash="hash",
        )

        parsed = adapter.parse(detail_result, self.context)
        confidence = calculate_confidence(parsed)

        self.assertEqual(parsed.title, "Advanced data platforms for clean energy")
        self.assertEqual(parsed.external_id, "HORIZON-TEST-OPEN")
        self.assertEqual(parsed.raw_metadata["source_status"], "open")
        self.assertEqual(parsed.application_open_at, datetime(2026, 5, 5, tzinfo=UTC))
        self.assertEqual(parsed.deadline_at, datetime(2026, 9, 15, tzinfo=UTC))
        self.assertEqual(parsed.country_codes, ("EU", "TR"))
        self.assertEqual(parsed.audience_keys, ("researcher",))
        self.assertFalse(confidence.requires_review)

    def result(self, body_text: str) -> FetchResult:
        item = DiscoveredItem(source_url=self.context.source_url, normalized_url=self.context.source_url)
        return FetchResult(
            item=item,
            final_url=self.context.source_url,
            status_code=200,
            content_type="application/json",
            body_text=body_text,
            fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
            content_hash="hash",
        )

    def api_response(self) -> str:
        return json.dumps(
            {
                "results": [
                    self.entry(
                        identifier="HORIZON-TEST-OPEN",
                        title="Advanced data platforms for clean energy",
                        status="31094502",
                        sort_status="1",
                        deadline="2026-09-15T00:00:00.000+0000",
                    ),
                    self.entry(
                        identifier="HORIZON-TEST-UPCOMING",
                        title="Future research infrastructure topic",
                        status="31094501",
                        sort_status="2",
                        deadline="2026-12-03T00:00:00.000+0000",
                    ),
                    self.entry(
                        identifier="HORIZON-TEST-CLOSED",
                        title="Closed legacy topic",
                        status="31094503",
                        sort_status="3",
                        deadline="2025-01-01T00:00:00.000+0000",
                    ),
                ]
            }
        )

    def entry(
        self,
        *,
        identifier: str,
        title: str,
        status: str,
        sort_status: str,
        deadline: str,
    ) -> dict[str, object]:
        return {
            "reference": f"{identifier}TOPICSen",
            "summary": title,
            "url": f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{identifier}",
            "metadata": {
                "identifier": [identifier],
                "title": [title],
                "url": [
                    "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/"
                    f"topic-details/{identifier}"
                ],
                "status": [status],
                "sortStatus": [sort_status],
                "startDate": ["2026-05-05T00:00:00.000+0000"],
                "deadlineDate": [deadline],
                "callIdentifier": ["HORIZON-TEST"],
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
                                "status": {"id": int(status), "description": "Open"},
                                "plannedOpeningDate": "2026-05-05",
                                "deadlineDates": [deadline[:10]],
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
