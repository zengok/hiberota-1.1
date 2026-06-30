# Controlled Backfill

Controlled backfill schedules source crawl tasks through Celery without bypassing source locks, source status, robots/terms metadata, or the normal crawler task entrypoint.

## Dry Run

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py schedule_controlled_backfill --limit=10
```

The dry run lists the planned sources and skips currently locked sources.

## Commit

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py schedule_controlled_backfill \
  --limit=10 \
  --countdown-step=30 \
  --queue=celery \
  --commit
```

The command enqueues `sources.crawl_source` tasks with spacing between source jobs.

## Narrow Scope

Use source keys for a smaller backfill:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py schedule_controlled_backfill \
  --source-key=tubitak_calls \
  --limit=1 \
  --commit
```

Paused sources are excluded by default. Include them only for a reviewed manual run:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
python manage.py schedule_controlled_backfill --include-paused --limit=5 --commit
```

## Rollback

Queued tasks cannot be safely removed generically after dispatch. To stop a backfill:

1. Pause affected `Source` rows in Django admin.
2. Stop or scale down the Celery worker if the run must be halted immediately.
3. Review source health and ingestion/review records before re-running.

Do not run broad backfills against production without a staging dry run and a small committed staging batch first.

## Production Scheduler Gate

Keep the production scheduler closed until the allowlist and rollback gate are explicitly reviewed:

```env
SOURCE_SCHEDULER_ENABLED=false
SOURCE_SCHEDULER_ROLLBACK_PAUSED=true
SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=true
SOURCE_SCHEDULER_ALLOWLIST=src-0011,src-0017
SOURCE_SCHEDULER_MAX_DUE_SOURCES=2
```

Opening sequence:

1. Confirm selected source keys are `active`, `robots_status=allowed`, and have recent controlled backfill evidence.
2. Set `SOURCE_SCHEDULER_ALLOWLIST` to only those source keys.
3. Keep `SOURCE_SCHEDULER_MAX_DUE_SOURCES` low for the first 72 hours.
4. Set `SOURCE_SCHEDULER_ROLLBACK_PAUSED=false`.
5. Set `SOURCE_SCHEDULER_ENABLED=true`.
6. Watch source health, review queue, queue depth, and public call quality after each beat cycle.

Rollback gate:

```env
SOURCE_SCHEDULER_ROLLBACK_PAUSED=true
```

This stops new scheduler dispatches without changing source rows or queued work already accepted by Celery.
