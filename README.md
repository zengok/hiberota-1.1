# HibeRota

HibeRota is a public, account-free grant and funding discovery platform built as a Django modular monolith.

## Stack

- Python 3.12
- Django 5.2 LTS
- PostgreSQL
- Redis
- Celery worker and Celery beat
- Bootstrap 5.3 with Django templates
- Gunicorn, Nginx, Docker Compose

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Start local PostgreSQL and Redis through Docker while keeping ports bound to localhost:

```bash
cp .env.local.example .env
POSTGRES_PASSWORD=hiberota_dev_password \
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d postgres redis
```

Then run Django commands from the host with:

```bash
python manage.py migrate
```

Health endpoints:

- `http://127.0.0.1:8000/health/live`
- `http://127.0.0.1:8000/health/ready`

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Nginx is exposed at `http://127.0.0.1:8080`.

For staging, use `staging.hiberota.com` and keep real secrets outside the repository:

```bash
cp .env.staging.example .env
docker compose up --build -d
```

The staging settings emit `X-Robots-Tag: noindex, nofollow`.
DNS is currently expected to be managed in Güzel Hosting; see `docs/GUZELHOSTING_DNS_CHECKLIST.md`.

Verify that the public staging URL is served by the Django staging stack before importing data:

```bash
python manage.py verify_staging_smoke
```

If staging TLS or the host Nginx vhost fails, apply `docs/STAGING_SSL_NGINX.md`
before continuing with source import.

## Development Checks

```bash
python manage.py check
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run
pytest
ruff check .
ruff format --check .
mypy .
bandit -r apps config automation
pip-audit
```

## Source Catalog Import

Validate a target-schema catalog without writing data:

```bash
python manage.py import_source_catalog /path/to/sources.csv
```

Apply the import after staging review:

```bash
python manage.py import_source_catalog /path/to/sources.csv --commit
```

See `docs/STAGING_SOURCE_IMPORT.md` for the staging runbook.

## Controlled Backfill

Preview a limited source backfill:

```bash
python manage.py schedule_controlled_backfill --limit=10
```

Queue the reviewed backfill:

```bash
python manage.py schedule_controlled_backfill --limit=10 --countdown-step=30 --commit
```

See `docs/CONTROLLED_BACKFILL.md` for staging and production guardrails.

## Call Data Quality

Check duplicate candidates and stale availability statuses:

```bash
python manage.py verify_call_data_quality --fail-on-issues
```

Require real checked calls, or run a rollback-only staging probe:

```bash
python manage.py verify_call_data_quality --require-checked
python manage.py verify_call_data_quality --probe
```

See `docs/CALL_DATA_QUALITY.md` for the verification scope.

## Staging Load Smoke

Run a small staging load smoke without extra benchmarking packages:

```bash
python manage.py run_staging_load_smoke --requests=60 --concurrency=4 --max-p95-ms=1500 --max-error-rate=0
```

## Project Boundaries

- No public user membership or profile system.
- No AI API integration in the MVP skeleton.
- PostgreSQL is the only production persistence source.
- Do not commit `.env`, real secrets, database dumps, generated media, or cache files.
