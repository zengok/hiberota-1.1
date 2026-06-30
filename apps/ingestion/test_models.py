from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.ingestion.models import CrawlItem, CrawlRun, FieldEvidence
from apps.institutions.models import Country, Institution
from apps.sources.models import Source


class FieldEvidenceModelTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.institution = Institution.objects.create(name="Kurum", slug="kurum", country=self.country)
        self.source = Source.objects.create(
            institution=self.institution,
            name="Kurum Duyurular",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="kurum_html_v1",
        )

    def test_evidence_confidence_cannot_exceed_100(self) -> None:
        call = GrantCall.objects.create(
            title="Test çağrısı",
            slug="test-cagrisi",
            source=self.source,
            institution=self.institution,
            official_url="https://example.org/calls/1",
            canonical_source_url="https://example.org/calls/1",
            fingerprint="fingerprint-1",
            first_seen_at=timezone.now(),
        )
        evidence = FieldEvidence(
            grant_call=call,
            field_name="title",
            source=self.source,
            source_url="https://example.org/calls/1",
            source_excerpt="Test çağrısı",
            fetched_at=timezone.now(),
            content_hash="hash-1",
            parser_version="parser-v1",
            confidence=101,
        )

        with self.assertRaises(ValidationError):
            evidence.full_clean()

    def test_crawl_run_and_item_store_crawl_metrics(self) -> None:
        run = CrawlRun.objects.create(
            source=self.source,
            trigger_type=CrawlRun.TriggerType.BACKFILL,
            status=CrawlRun.Status.RUNNING,
            started_at=timezone.now(),
            discovered_count=1,
            fetched_count=1,
            http_status_summary={"200": 1},
            config_version=self.source.config_version,
        )
        item = CrawlItem.objects.create(
            crawl_run=run,
            source_url="https://example.org/calls/1",
            normalized_url="https://example.org/calls/1",
            status=CrawlItem.Status.FETCHED,
            attempt_count=1,
            http_status=200,
            parser_version="parser-v1",
            raw_metadata_json={"source": "fixture"},
        )

        self.assertEqual(str(run), f"{self.source.id}:backfill:running")
        self.assertEqual(item.crawl_run, run)
        self.assertEqual(item.raw_metadata_json["source"], "fixture")
