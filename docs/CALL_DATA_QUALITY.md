# Call Data Quality Verification

This check reports duplicate candidates and stale availability statuses after staging import or backfill.

## Run

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py verify_call_data_quality
```

Limit the check to reviewed sources:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py verify_call_data_quality --source-key=tubitak_calls
```

Fail the command when issues are found:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py verify_call_data_quality --fail-on-issues
```

## What It Checks

- semantic duplicate candidates by institution, normalized title, and deadline date,
- stale `availability_status` values compared with open/deadline dates.

The command does not mutate data. Resolve findings through review/admin workflows, then re-run the check.
