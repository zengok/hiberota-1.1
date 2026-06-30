from __future__ import annotations

from email.message import Message
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.institutions.models import Country, Institution
from apps.sources.compliance import apply_robots_check_result, check_source_robots
from apps.sources.models import Source


class SourceRobotsComplianceTests(TestCase):
    def setUp(self) -> None:
        country = Country.objects.create(code="TR", name_tr="Turkiye", name_en="Turkey")
        institution = Institution.objects.create(country=country, name="Kurum", slug="kurum")
        self.source = Source.objects.create(
            institution=institution,
            source_key="source-a",
            name="Source A",
            base_url="https://example.org/path",
            listing_url="https://example.org/public/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="source_a_html_v1",
            status=Source.Status.ACTIVE,
            crawl_interval_minutes=60,
            robots_status=Source.RobotsStatus.UNKNOWN,
            terms_status=Source.TermsStatus.UNKNOWN,
        )

    def test_allowed_robots_result(self) -> None:
        response = SimpleNamespace(body=b"User-agent: *\nAllow: /\n")

        with patch("apps.sources.compliance.fetch_url_with_retries", return_value=response):
            result = check_source_robots(self.source, now=timezone.now())

        self.assertEqual(result.status, Source.RobotsStatus.ALLOWED)
        self.assertEqual(result.robots_url, "https://example.org/robots.txt")

    def test_restricted_robots_result(self) -> None:
        response = SimpleNamespace(body=b"User-agent: *\nDisallow: /public\n")

        with patch("apps.sources.compliance.fetch_url_with_retries", return_value=response):
            result = check_source_robots(self.source, now=timezone.now())

        self.assertEqual(result.status, Source.RobotsStatus.RESTRICTED)

    def test_http_403_marks_restricted(self) -> None:
        error = HTTPError("https://example.org/robots.txt", 403, "Forbidden", hdrs=Message(), fp=None)

        with patch("apps.sources.compliance.fetch_url_with_retries", side_effect=error):
            result = check_source_robots(self.source, now=timezone.now())

        self.assertEqual(result.status, Source.RobotsStatus.RESTRICTED)
        self.assertEqual(result.error, "http_403")

    def test_apply_result_updates_source_config(self) -> None:
        response = SimpleNamespace(body=b"User-agent: *\nAllow: /\n")
        with patch("apps.sources.compliance.fetch_url_with_retries", return_value=response):
            result = check_source_robots(self.source, now=timezone.now())

        apply_robots_check_result(self.source, result)

        self.source.refresh_from_db()
        self.assertEqual(self.source.robots_status, Source.RobotsStatus.ALLOWED)
        self.assertEqual(self.source.config_json["robots_check"]["status"], Source.RobotsStatus.ALLOWED)
        self.assertEqual(self.source.config_version, 2)

    def test_management_command_dry_run_does_not_update(self) -> None:
        response = SimpleNamespace(body=b"User-agent: *\nAllow: /\n")

        with patch("apps.sources.compliance.fetch_url_with_retries", return_value=response):
            output = StringIO()
            call_command("verify_source_robots", "--source-key=source-a", stdout=output)

        self.source.refresh_from_db()
        self.assertEqual(self.source.robots_status, Source.RobotsStatus.UNKNOWN)
        self.assertIn("Dry run complete", output.getvalue())
