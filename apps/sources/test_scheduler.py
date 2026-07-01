from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from apps.institutions.models import Country, Institution
from apps.sources.locks import CrawlLock
from apps.sources.models import Source
from apps.sources.scheduler import due_sources, scheduler_can_run
from apps.sources.tasks import schedule_due_sources


class SchedulerTests(TestCase):
    def setUp(self) -> None:
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.institution = Institution.objects.create(name="Kurum", slug="kurum", country=self.country)

    def create_source(self, **overrides: object) -> Source:
        source_key = str(overrides.get("source_key") or f"source-{Source.objects.count() + 1}")
        values = {
            "institution": self.institution,
            "name": "Kurum Duyurular",
            "base_url": "https://example.org",
            "listing_url": f"https://example.org/calls/{source_key}",
            "source_type": Source.SourceType.HTML,
            "adapter_key": f"{source_key}_html_v1",
        } | overrides
        return Source.objects.create(**values)

    def test_due_sources_include_never_crawled_active_source(self) -> None:
        source = self.create_source()

        self.assertEqual(due_sources(), [source])

    def test_due_sources_exclude_recently_successful_source(self) -> None:
        self.create_source(last_success_at=timezone.now(), crawl_interval_minutes=60)

        self.assertEqual(due_sources(), [])

    def test_due_sources_include_old_successful_source(self) -> None:
        source = self.create_source(last_success_at=timezone.now() - timedelta(hours=2), crawl_interval_minutes=60)

        self.assertEqual(due_sources(), [source])

    def test_due_sources_exclude_recently_failed_source(self) -> None:
        self.create_source(last_failure_at=timezone.now(), crawl_interval_minutes=60)

        self.assertEqual(due_sources(), [])

    def test_due_sources_include_old_failed_source(self) -> None:
        source = self.create_source(last_failure_at=timezone.now() - timedelta(hours=2), crawl_interval_minutes=60)

        self.assertEqual(due_sources(), [source])

    @override_settings(SOURCE_SCHEDULER_ALLOWLIST=("source-b",))
    def test_due_sources_apply_scheduler_allowlist(self) -> None:
        self.create_source(source_key="source-a", name="Source A")
        source = self.create_source(source_key="source-b", name="Source B")

        self.assertEqual(due_sources(), [source])

    def test_due_sources_prioritize_turkey_then_europe_then_other_regions(self) -> None:
        europe_country = Country.objects.create(code="DE", name_tr="Almanya", name_en="Germany", is_europe=True)
        other_country = Country.objects.create(code="US", name_tr="ABD", name_en="United States", is_europe=False)
        europe_institution = Institution.objects.create(name="EU Kurum", slug="eu-kurum", country=europe_country)
        other_institution = Institution.objects.create(name="US Kurum", slug="us-kurum", country=other_country)
        other = self.create_source(
            source_key="source-us",
            name="US Source",
            institution=other_institution,
            config_json={"priority": 1},
        )
        europe = self.create_source(
            source_key="source-de",
            name="DE Source",
            institution=europe_institution,
            config_json={"priority": 1},
        )
        turkey = self.create_source(source_key="source-tr", name="TR Source", config_json={"priority": 9})

        self.assertEqual(due_sources(), [turkey, europe, other])

    def test_due_sources_order_by_catalog_priority_inside_region(self) -> None:
        low_priority = self.create_source(
            source_key="source-low",
            name="Low Priority",
            config_json={"priority": 20},
        )
        high_priority = self.create_source(
            source_key="source-high",
            name="High Priority",
            config_json={"priority": 1},
        )

        self.assertEqual(due_sources(), [high_priority, low_priority])

    def test_crawl_lock_allows_single_holder(self) -> None:
        cache.clear()
        lock = CrawlLock(source_id=1)

        self.assertTrue(lock.acquire())
        self.assertFalse(lock.acquire())
        lock.release()
        self.assertTrue(lock.acquire())

    @override_settings(SOURCE_SCHEDULER_ENABLED=False)
    def test_schedule_due_sources_returns_zero_when_scheduler_disabled(self) -> None:
        self.create_source()

        self.assertEqual(schedule_due_sources(), 0)

    @override_settings(SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=True, SOURCE_SCHEDULER_ALLOWLIST=())
    def test_schedule_due_sources_requires_allowlist_when_gate_is_enabled(self) -> None:
        self.create_source()

        self.assertFalse(scheduler_can_run())
        self.assertEqual(schedule_due_sources(), 0)

    @override_settings(SOURCE_SCHEDULER_ROLLBACK_PAUSED=True)
    def test_schedule_due_sources_returns_zero_when_rollback_gate_is_paused(self) -> None:
        self.create_source()

        self.assertFalse(scheduler_can_run())
        self.assertEqual(schedule_due_sources(), 0)

    @override_settings(SOURCE_SCHEDULER_ALLOWLIST=("source-a", "source-b"), SOURCE_SCHEDULER_MAX_DUE_SOURCES=1)
    def test_schedule_due_sources_respects_max_due_sources(self) -> None:
        first = self.create_source(source_key="source-a", name="Source A")
        self.create_source(source_key="source-b", name="Source B")

        with patch("apps.sources.tasks.crawl_source.delay") as delay:
            queued = schedule_due_sources()

        self.assertEqual(queued, 1)
        delay.assert_called_once_with(first.id)
