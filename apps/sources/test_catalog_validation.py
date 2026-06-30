from __future__ import annotations

from django.test import SimpleTestCase

from apps.sources.catalog_validation import validate_source_catalog_rows

VALID_HEADERS = [
    "source_key",
    "institution_name",
    "country_code",
    "source_name",
    "base_url",
    "listing_url",
    "source_type",
    "adapter_key",
    "crawl_interval_minutes",
    "language_codes",
    "robots_status",
    "terms_status",
    "enabled",
]


VALID_ROW = {
    "source_key": "tubitak_calls",
    "institution_name": "TÜBİTAK",
    "country_code": "TR",
    "source_name": "TÜBİTAK Duyurular",
    "base_url": "https://www.tubitak.gov.tr",
    "listing_url": "https://www.tubitak.gov.tr/tr/duyurular",
    "source_type": "html",
    "adapter_key": "tubitak_html_v1",
    "crawl_interval_minutes": 60,
    "language_codes": "tr",
    "robots_status": "allowed",
    "terms_status": "reviewed",
    "enabled": "true",
}


class SourceCatalogValidationTests(SimpleTestCase):
    def test_valid_source_catalog_row_passes(self) -> None:
        result = validate_source_catalog_rows([VALID_ROW], VALID_HEADERS)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, ())

    def test_missing_required_header_fails(self) -> None:
        headers = [header for header in VALID_HEADERS if header != "source_key"]

        result = validate_source_catalog_rows([VALID_ROW], headers)

        self.assertFalse(result.is_valid)
        self.assertIn("source_key", result.missing_columns)

    def test_duplicate_source_key_fails(self) -> None:
        result = validate_source_catalog_rows([VALID_ROW, VALID_ROW], VALID_HEADERS)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "duplicate_source_key" for issue in result.issues))

    def test_secret_like_value_fails(self) -> None:
        secret_like_value = "sk-" + "123456789012345678901234"
        row = VALID_ROW | {"config_json": f'{{"api_key": "{secret_like_value}"}}'}

        result = validate_source_catalog_rows([row], VALID_HEADERS + ["config_json"])

        self.assertFalse(result.is_valid)
        self.assertTrue(any(issue.code == "secret_like_value" for issue in result.issues))

    def test_legacy_workbook_headers_are_not_target_schema_ready(self) -> None:
        legacy_headers = ["source_id", "institution", "country_iso2", "portal_name", "source_url"]

        result = validate_source_catalog_rows([], legacy_headers)

        self.assertFalse(result.is_valid)
        self.assertIn("source_key", result.missing_columns)
        self.assertIn("source_id", result.unknown_columns)
