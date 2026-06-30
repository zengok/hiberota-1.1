# Implementation Note — Phase 0/1 Skeleton

Scope for this slice:

- Inventory existing non-code project assets by filename, size, and intended use only.
- Create a Django 5.2 / Python 3.12 project skeleton with environment-based settings.
- Add Docker Compose services for web, PostgreSQL, Redis, Celery worker, Celery beat, and Nginx.
- Add healthcheck endpoints and baseline quality tooling.
- Do not add public accounts, AI integrations, production deploy state, or real secrets.

Validation target:

- Django system checks pass locally.
- Tests pass for health endpoints.
- Ruff, format check, mypy, Bandit, and pip-audit are runnable from the repo.
