from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.institutions.models import Country, Institution
from apps.sources.locks import CrawlLock
from apps.sources.models import Source


class ScheduleControlledBackfillCommandTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")

    def test_dry_run_does_not_enqueue_tasks(self) -> None:
        self._create_source("source-a")

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            output = StringIO()
            call_command("schedule_controlled_backfill", stdout=output)

        task.assert_not_called()
        self.assertIn("Dry run complete", output.getvalue())

    def test_commit_enqueues_limited_active_sources_with_spacing(self) -> None:
        first = self._create_source("source-a")
        second = self._create_source("source-b")
        self._create_source("source-c")

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            call_command(
                "schedule_controlled_backfill",
                "--limit=2",
                "--countdown-step=15",
                "--queue=backfill",
                "--commit",
                stdout=StringIO(),
            )

        self.assertEqual(task.call_count, 2)
        task.assert_any_call(args=[first.id], countdown=0, queue="backfill")
        task.assert_any_call(args=[second.id], countdown=15, queue="backfill")

    def test_source_key_filter_limits_backfill_plan(self) -> None:
        self._create_source("source-a")
        selected = self._create_source("source-b")

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            call_command("schedule_controlled_backfill", "--source-key=source-b", "--commit", stdout=StringIO())

        task.assert_called_once_with(args=[selected.id], countdown=0, queue="celery")

    def test_paused_sources_require_explicit_include_flag(self) -> None:
        paused = self._create_source("source-paused", status=Source.Status.PAUSED)

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            call_command("schedule_controlled_backfill", "--commit", stdout=StringIO())
        task.assert_not_called()

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            call_command(
                "schedule_controlled_backfill",
                "--include-paused",
                "--commit",
                stdout=StringIO(),
            )
        task.assert_called_once_with(args=[paused.id], countdown=0, queue="celery")

    def test_locked_sources_are_skipped(self) -> None:
        locked = self._create_source("source-locked")
        available = self._create_source("source-available")
        self.assertTrue(CrawlLock(source_id=locked.id).acquire())

        with patch("apps.sources.management.commands.schedule_controlled_backfill.crawl_source.apply_async") as task:
            output = StringIO()
            call_command("schedule_controlled_backfill", "--commit", stdout=output)

        task.assert_called_once_with(args=[available.id], countdown=0, queue="celery")
        self.assertIn("Skipped locked sources: 1", output.getvalue())

    def test_limit_is_bounded(self) -> None:
        with self.assertRaises(CommandError):
            call_command("schedule_controlled_backfill", "--limit=101", stdout=StringIO())

    def _create_source(self, source_key: str, status: str = Source.Status.ACTIVE) -> Source:
        return Source.objects.create(
            institution=self.institution,
            source_key=source_key,
            name=source_key,
            base_url="https://example.org",
            listing_url=f"https://example.org/{source_key}",
            source_type=Source.SourceType.HTML,
            adapter_key=f"{source_key}_html_v1",
            status=status,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.ALLOWED,
            terms_status=Source.TermsStatus.REVIEWED,
        )
