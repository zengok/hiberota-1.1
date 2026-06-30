# Staging Source Catalog Import

This runbook imports a target-schema source catalog into the staging PostgreSQL database.

## Input

Use a UTF-8 CSV that matches `data/SOURCE_CATALOG_SCHEMA.md`.

The repository workbook is not read on every runtime cycle. If the workbook is the source input, convert it to the target schema first, then run the validation/import command below.

## Dry Run

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py import_source_catalog /secure/path/sources.csv
```

The dry run validates rows, reports warnings, and shows how many sources would be created or updated.

## Commit

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py import_source_catalog /secure/path/sources.csv --commit
```

The command writes in a single transaction:

- `Country` rows by ISO alpha-2 code,
- verified `Institution` rows by country and institution name,
- `Source` rows by stable `source_key`.

Disabled catalog rows are imported as paused sources so the scheduler does not crawl them.

## Rollback

If the import needs to be reverted before production launch:

1. Restore the staging database snapshot taken before the import.
2. Or pause affected sources by `source_key` in Django admin.
3. Re-run the dry run with the corrected catalog before any new commit.

Do not store staging credentials, API keys, cookies, or private source credentials in the CSV.
