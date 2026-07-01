from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify

from apps.institutions.models import Country, Institution
from apps.sources.catalog_validation import CatalogValidationIssue, validate_source_catalog_rows
from apps.sources.models import Source

EUROPE_COUNTRY_CODES = {
    "AD",
    "AL",
    "AT",
    "BA",
    "BE",
    "BG",
    "BY",
    "CH",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "ES",
    "EU",
    "FI",
    "FR",
    "GB",
    "GR",
    "HR",
    "HU",
    "IE",
    "IS",
    "IT",
    "LI",
    "LT",
    "LU",
    "LV",
    "MC",
    "MD",
    "ME",
    "MK",
    "MT",
    "NL",
    "NO",
    "PL",
    "PT",
    "RO",
    "RS",
    "SE",
    "SI",
    "SK",
    "TR",
    "UA",
    "VA",
}


@dataclass(frozen=True, slots=True)
class ImportSummary:
    rows: int
    countries_created: int = 0
    institutions_created: int = 0
    institutions_updated: int = 0
    sources_created: int = 0
    sources_updated: int = 0
    sources_paused: int = 0


class Command(BaseCommand):
    help = "Validate and import a source catalog CSV into Source records."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("catalog_path", type=Path)
        parser.add_argument("--commit", action="store_true", help="Apply changes. Omit for validation-only dry run.")

    def handle(self, *args: Any, **options: Any) -> None:
        catalog_path = Path(options["catalog_path"])
        rows, headers = _read_csv_catalog(catalog_path)
        result = validate_source_catalog_rows(rows, headers)

        self.stdout.write(f"Rows read: {result.row_count}")
        if result.warnings:
            self.stdout.write("Warnings:")
            for warning in result.warnings:
                self.stdout.write(_format_issue(warning))

        if not result.is_valid:
            self.stderr.write("Validation failed:")
            for issue in result.issues:
                self.stderr.write(_format_issue(issue))
            raise CommandError("Source catalog validation failed.")

        if not options["commit"]:
            planned = _build_dry_run_summary(rows)
            self.stdout.write(
                self.style.SUCCESS(
                    "Dry run complete: "
                    f"{planned.rows} rows, "
                    f"{planned.sources_created} sources to create, "
                    f"{planned.sources_updated} sources to update."
                )
            )
            self.stdout.write("Run again with --commit to apply changes.")
            return

        with transaction.atomic():
            summary = _import_rows(rows)

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete: "
                f"{summary.rows} rows, "
                f"{summary.countries_created} countries created, "
                f"{summary.institutions_created} institutions created, "
                f"{summary.institutions_updated} institutions updated, "
                f"{summary.sources_created} sources created, "
                f"{summary.sources_updated} sources updated, "
                f"{summary.sources_paused} sources paused."
            )
        )


def _read_csv_catalog(catalog_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if catalog_path.suffix.lower() != ".csv":
        raise CommandError("Only target-schema CSV files are supported by this command.")

    if not catalog_path.exists() or not catalog_path.is_file():
        raise CommandError("Catalog CSV file was not found.")

    with catalog_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]

    if not headers:
        raise CommandError("Catalog CSV must include a header row.")

    return rows, headers


def _format_issue(issue: CatalogValidationIssue) -> str:
    return f"row {issue.row_number}, {issue.column}: {issue.code} - {issue.message}"


def _build_dry_run_summary(rows: list[dict[str, Any]]) -> ImportSummary:
    source_keys = [str(row["source_key"]).strip() for row in rows]
    existing_keys = set(Source.objects.filter(source_key__in=source_keys).values_list("source_key", flat=True))
    return ImportSummary(
        rows=len(rows),
        sources_created=sum(1 for key in source_keys if key not in existing_keys),
        sources_updated=sum(1 for key in source_keys if key in existing_keys),
    )


def _import_rows(rows: list[dict[str, Any]]) -> ImportSummary:
    summary = ImportSummary(rows=len(rows))
    mutable_summary = {
        "countries_created": 0,
        "institutions_created": 0,
        "institutions_updated": 0,
        "sources_created": 0,
        "sources_updated": 0,
        "sources_paused": 0,
    }

    for row in rows:
        country_code = _clean(row["country_code"]).upper()
        region_code = _clean(row.get("region_code"))
        country, country_created = Country.objects.get_or_create(
            code=country_code,
            defaults={
                "name_tr": country_code,
                "name_en": country_code,
                "region_code": region_code,
                "is_europe": _is_europe_country(country_code=country_code, region_code=region_code),
                "is_eu_member": country_code == "EU",
            },
        )
        if country_created:
            mutable_summary["countries_created"] += 1
        else:
            country_updates = []
            is_europe = _is_europe_country(country_code=country_code, region_code=region_code)
            if region_code and country.region_code != region_code:
                country.region_code = region_code
                country_updates.append("region_code")
            if country.is_europe != is_europe:
                country.is_europe = is_europe
                country_updates.append("is_europe")
            if country_code == "EU" and not country.is_eu_member:
                country.is_eu_member = True
                country_updates.append("is_eu_member")
            if country_updates:
                country.save(update_fields=[*country_updates, "updated_at"])

        institution, institution_created = Institution.objects.update_or_create(
            country=country,
            name=_clean(row["institution_name"]),
            defaults={
                "slug": _unique_institution_slug(country, _clean(row["institution_name"])),
                "short_name": _clean(row.get("institution_short_name")),
                "website_url": _clean(row["base_url"]),
                "is_verified": True,
                "is_active": True,
            },
        )
        if institution_created:
            mutable_summary["institutions_created"] += 1
        else:
            mutable_summary["institutions_updated"] += 1

        config = _catalog_config(row)
        source, source_created = Source.objects.update_or_create(
            source_key=_clean(row["source_key"]),
            defaults={
                "institution": institution,
                "name": _clean(row["source_name"]),
                "base_url": _clean(row["base_url"]),
                "listing_url": _clean(row["listing_url"]),
                "source_type": _clean(row["source_type"]),
                "adapter_key": _clean(row["adapter_key"]),
                "status": Source.Status.ACTIVE if _parse_bool(row["enabled"]) else Source.Status.PAUSED,
                "crawl_interval_minutes": int(_clean(row["crawl_interval_minutes"])),
                "robots_status": _clean(row["robots_status"]),
                "terms_status": _clean(row["terms_status"]),
                "contact_url": _clean(row.get("contact_url")),
                "config_json": config,
            },
        )
        if source_created:
            mutable_summary["sources_created"] += 1
        else:
            source.config_version += 1
            source.save(update_fields=["config_version", "updated_at"])
            mutable_summary["sources_updated"] += 1

        if source.status == Source.Status.PAUSED:
            mutable_summary["sources_paused"] += 1

    return ImportSummary(rows=summary.rows, **mutable_summary)


def _unique_institution_slug(country: Country, name: str) -> str:
    base_slug = slugify(name, allow_unicode=False) or country.code.lower()
    slug = base_slug
    suffix = 2
    while Institution.objects.filter(slug=slug).exclude(country=country, name=name).exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def _catalog_config(row: dict[str, Any]) -> dict[str, Any]:
    raw_config = _clean(row.get("config_json"))
    config: dict[str, Any] = json.loads(raw_config) if raw_config else {}
    config["language_codes"] = _split_csv_value(row.get("language_codes"))
    config["audience_hints"] = _split_csv_value(row.get("audience_hints"))
    config["source_catalog"] = {
        "api_docs_url": _clean(row.get("api_docs_url")),
        "rss_feed_url": _clean(row.get("rss_feed_url")),
        "robots_checked_at": _clean(row.get("robots_checked_at")),
        "notes": _clean(row.get("notes")),
    }
    institution_name = _clean(row.get("institution_name"))
    if institution_name and not config.get("institution_name_override"):
        config["institution_name_override"] = institution_name
    country_code = _clean(row.get("country_code")).upper()
    if country_code and country_code not in {"XX", ""} and not config.get("country_codes_override"):
        config["country_codes_override"] = [country_code]
    return config


def _split_csv_value(value: Any) -> list[str]:
    return [item.strip() for item in _clean(value).split(",") if item.strip()]


def _parse_bool(value: Any) -> bool:
    return _clean(value).lower() in {"true", "1", "yes"}


def _is_europe_country(*, country_code: str, region_code: str) -> bool:
    return region_code.casefold() == "europe" or country_code in EUROPE_COUNTRY_CODES


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()
