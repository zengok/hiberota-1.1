from __future__ import annotations

from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from apps.core.management.commands.run_staging_load_smoke import LoadSample, summarize_samples


class StagingLoadSmokeTests(SimpleTestCase):
    def test_summarize_samples_reports_p95_and_failures(self) -> None:
        samples = [
            LoadSample(path="/", status_code=200, elapsed_ms=100),
            LoadSample(path="/", status_code=200, elapsed_ms=200),
            LoadSample(path="/health/live", status_code=503, elapsed_ms=300),
        ]

        summary = summarize_samples(samples)

        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.failures, 1)
        self.assertAlmostEqual(summary.error_rate, 1 / 3)
        self.assertEqual(summary.p95_ms, 200)
        self.assertEqual(summary.max_ms, 300)

    @patch("apps.core.management.commands.run_staging_load_smoke._fetch_once")
    def test_command_fails_when_error_rate_exceeds_threshold(self, fetch_once: Mock) -> None:
        fetch_once.side_effect = [
            LoadSample(path="/", status_code=200, elapsed_ms=100),
            LoadSample(path="/health/live", status_code=503, elapsed_ms=120, error="HTTP 503"),
        ]

        with self.assertRaises(CommandError):
            call_command(
                "run_staging_load_smoke",
                "--base-url=https://staging.example.test",
                "--requests=2",
                "--concurrency=1",
                "--max-error-rate=0",
                stdout=StringIO(),
            )

    @patch("apps.core.management.commands.run_staging_load_smoke._fetch_once")
    def test_command_passes_when_thresholds_hold(self, fetch_once: Mock) -> None:
        fetch_once.side_effect = [
            LoadSample(path="/", status_code=200, elapsed_ms=100),
            LoadSample(path="/health/live", status_code=200, elapsed_ms=120),
        ]
        output = StringIO()

        call_command(
            "run_staging_load_smoke",
            "--base-url=https://staging.example.test",
            "--requests=2",
            "--concurrency=1",
            "--max-p95-ms=500",
            stdout=output,
        )

        self.assertIn("Staging load smoke passed", output.getvalue())
