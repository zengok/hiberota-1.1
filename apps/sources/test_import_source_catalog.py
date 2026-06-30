from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.institutions.models import Country, Institution
from apps.sources.models import Source

CATALOG_ROW = {
    "source_key": "tubitak_calls",
    "institution_name": "TUBITAK",
    "institution_short_name": "TUBITAK",
    "country_code": "TR",
    "region_code": "europe",
    "source_name": "TUBITAK Duyurular",
    "base_url": "https://www.tubitak.gov.tr",
    "listing_url": "https://www.tubitak.gov.tr/tr/duyurular",
    "source_type": "html",
    "adapter_key": "tubitak_html_v1",
    "crawl_interval_minutes": "60",
    "language_codes": "tr,en",
    "audience_hints": "researcher,sme",
    "robots_checked_at": "2026-06-25",
    "robots_status": "allowed",
    "terms_status": "reviewed",
    "api_docs_url": "",
    "rss_feed_url": "",
    "contact_url": "https://www.tubitak.gov.tr/tr/kurumsal/iletisim",
    "enabled": "true",
    "notes": "Official public announcements",
    "config_json": '{"priority": "high"}',
}


class ImportSourceCatalogCommandTests(TestCase):
    def test_dry_run_validates_without_writing(self) -> None:
        catalog_path = _write_catalog([CATALOG_ROW])
        output = StringIO()

        call_command("import_source_catalog", catalog_path, stdout=output)

        self.assertIn("Dry run complete", output.getvalue())
        self.assertEqual(Source.objects.count(), 0)
        self.assertEqual(Institution.objects.count(), 0)
        self.assertEqual(Country.objects.count(), 0)

    def test_commit_imports_catalog_rows(self) -> None:
        catalog_path = _write_catalog([CATALOG_ROW])

        call_command("import_source_catalog", catalog_path, "--commit", stdout=StringIO())

        source = Source.objects.get(source_key="tubitak_calls")
        self.assertEqual(source.name, "TUBITAK Duyurular")
        self.assertEqual(source.status, Source.Status.ACTIVE)
        self.assertEqual(source.config_json["language_codes"], ["tr", "en"])
        self.assertEqual(source.config_json["audience_hints"], ["researcher", "sme"])
        self.assertEqual(source.config_json["priority"], "high")
        self.assertEqual(source.institution.country.code, "TR")
        self.assertTrue(source.institution.is_verified)

    def test_commit_updates_existing_source_and_increments_config_version(self) -> None:
        catalog_path = _write_catalog([CATALOG_ROW])
        call_command("import_source_catalog", catalog_path, "--commit", stdout=StringIO())

        updated_path = _write_catalog([CATALOG_ROW | {"source_name": "TUBITAK Cagri Listesi", "enabled": "false"}])
        call_command("import_source_catalog", updated_path, "--commit", stdout=StringIO())

        source = Source.objects.get(source_key="tubitak_calls")
        self.assertEqual(source.name, "TUBITAK Cagri Listesi")
        self.assertEqual(source.status, Source.Status.PAUSED)
        self.assertEqual(source.config_version, 2)
        self.assertEqual(Source.objects.count(), 1)

    def test_invalid_catalog_fails_before_writing(self) -> None:
        catalog_path = _write_catalog([CATALOG_ROW | {"source_key": "bad key"}])

        with self.assertRaises(CommandError):
            call_command("import_source_catalog", catalog_path, "--commit", stdout=StringIO(), stderr=StringIO())

        self.assertEqual(Source.objects.count(), 0)


def _write_catalog(rows: list[dict[str, str]]) -> Path:
    directory = TemporaryDirectory()
    path = Path(directory.name) / "sources.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CATALOG_ROW.keys()))
        writer.writeheader()
        writer.writerows(rows)
    _TEMP_DIRS.append(directory)
    return path


_TEMP_DIRS: list[TemporaryDirectory[str]] = []
