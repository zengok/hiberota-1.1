#!/bin/sh
set -e

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

# Only the web (gunicorn) container handles static files and catalog import.
# Celery worker/beat containers share the same image but skip these steps.
case "$1" in
  gunicorn*)
    echo "[entrypoint] Collecting static files..."
    python manage.py collectstatic --noinput --clear

    echo "[entrypoint] Importing source catalog..."
    python manage.py import_source_catalog data/source_catalog_import.csv --commit || true
    ;;
esac

echo "[entrypoint] Starting: $*"
exec "$@"
