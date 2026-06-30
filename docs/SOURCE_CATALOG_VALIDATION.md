# Source Catalog Validation

Validation date: 2026-06-25

Workbook checked: `../HibeRota_Global_Call_Portals_2026.xlsx`

The original workbook was not modified. The check read workbook metadata, sheet names, headers, the first 5 sample rows, and aggregate row-level validation results.

## Workbook Structure

Sheets:

- `Call_Portals`
- `Data_Dictionary`
- `Import_Guide`
- `Coverage_Summary`

Primary data sheet found: `Call_Portals`

Record count in `Call_Portals`: 249

## Current Header Row

```text
source_id
region
subregion
country
country_iso2
institution
portal_name
source_url
funding_scope
source_type
access_method
priority
check_frequency_hours
requires_javascript
requires_login
language
geographic_scope
coverage_role
is_official
integration_status
verified_on
technical_notes
```

## Result

Status: not directly import-ready for the current target schema in `data/SOURCE_CATALOG_SCHEMA.md`.

The workbook is a useful source registry, but its current column names and meanings are closer to a raw portal inventory than the target `sources` import contract.

## Target Schema Gaps

Missing required target columns:

- `source_key`
- `institution_name`
- `country_code`
- `source_name`
- `base_url`
- `listing_url`
- `adapter_key`
- `crawl_interval_minutes`
- `language_codes`
- `robots_status`
- `terms_status`
- `enabled`

Missing optional target columns:

- `institution_short_name`
- `region_code`
- `audience_hints`
- `robots_checked_at`
- `api_docs_url`
- `rss_feed_url`
- `contact_url`
- `notes`
- `config_json`

## Existing Data Quality Checks

- Duplicate `source_id`: 0 found.
- Invalid `source_url`: 0 found.
- Secret-like token/key patterns: 0 found.
- `requires_login`: 3 rows are marked true and must be reviewed before any adapter work.

Observed `access_method` values:

- `html`: 241
- `javascript`: 6
- `api_or_javascript`: 1
- `api_or_html`: 1

Observed current `source_type` values are portal categories such as `agency_portal`, `national_single_portal`, and `programme_portal`; these do not match the target enum `api/feed/sitemap/html/headless/manual`.

## Required Mapping Before Import

Recommended mapping for a future importer:

| Current workbook column | Target schema column | Note |
|---|---|---|
| `source_id` | `source_key` | Direct rename. |
| `institution` | `institution_name` | Direct rename. |
| `country_iso2` | `country_code` | Needs policy for `XX` global and `EU` regional values. |
| `portal_name` | `source_name` | Direct rename. |
| `source_url` | `base_url`, `listing_url` | Listing URL can initially equal source URL, but base domain should be normalized. |
| `access_method` | `source_type` | Map `html` to `html`; review JavaScript/API mixed values. |
| `check_frequency_hours` | `crawl_interval_minutes` | Convert hours to minutes. |
| `language` | `language_codes` | Convert names like `English` to codes like `en`. |
| `verified_on` | `robots_checked_at` | Only valid if it actually means robots/terms review date; otherwise keep separate. |
| `technical_notes` | `notes` | Direct rename. |

Fields that need defaulting or manual enrichment:

- `adapter_key`
- `robots_status`
- `terms_status`
- `enabled`
- `audience_hints`
- `config_json`

## Decision

Do not import this workbook directly into `Source` records yet. First build a controlled validation/import command that maps the current workbook format into the target schema, reports the 3 login-required rows, and requires human approval before applying changes.
