# ADR-001 — Technical Stack and Modular Monolith

Status: Accepted

Date: 2026-06-25

## Context

HibeRota needs to collect grant and funding calls from official sources, normalize and review them, and publish SEO-friendly public pages without requiring public user accounts.

The first production target is a constrained VDS-class deployment. The system needs strong admin tooling, server-rendered public pages, reliable background jobs, PostgreSQL-backed data integrity, and an architecture that remains simple enough to operate and evolve.

## Decision

HibeRota will use the following baseline stack:

- Backend and server-rendered web: Django 5.2 LTS.
- Runtime language: Python 3.12.
- Persistent production data store: PostgreSQL.
- Queue broker and short-lived cache: Redis.
- Background jobs: Celery worker and Celery beat.
- Web runtime: Gunicorn behind Nginx.
- Frontend: Django templates, Bootstrap 5.3, and limited Vanilla JavaScript.
- Search and filtering: PostgreSQL full-text search and `pg_trgm`.
- Production packaging and deployment unit: Docker Compose.
- Edge/CDN/WAF/DDoS layer: Cloudflare.

The application will be a Django modular monolith. Domain boundaries are represented as Django apps and Python packages, not separate services.

Public visitors will not have accounts or profiles. Public favorites and survey preferences may use browser `localStorage` only and must not store sensitive data.

MVP data extraction and matching will not use an AI API. Future AI support may be added only behind a separate extension interface and a new ADR.

SQLite is not a production persistence layer. PostgreSQL is the only production source of truth for application state, automation state, review state, and audit history.

## Consequences

Positive:

- Lower operational complexity for the first production environment.
- Native Django admin and ORM support for management workflows.
- Server-rendered pages align with SEO and accessibility goals.
- Celery and Redis support crawl, publication, newsletter, and maintenance jobs without introducing service sprawl.
- PostgreSQL keeps source, crawl, review, duplicate, content, and audit records in one transactional store.

Tradeoffs:

- Scaling is vertical and queue-oriented first, not microservice-oriented.
- Components must keep module boundaries clean to avoid a tangled monolith.
- Heavy future search, media, notification, or worker workloads may need measured extraction later.

## Non-Goals

- Public account/profile implementation.
- AI API integration.
- Production SQLite usage.
- Microservice extraction before measured need.
- Bypassing source robots, terms, CAPTCHA, login walls, anti-bot controls, or access restrictions.

## Change Control

Changing any baseline technology listed in this ADR requires:

1. A new or superseding ADR.
2. Clear operational or product evidence.
3. Human approval before implementation.

Potential future extractions such as a search service, object storage, dedicated worker host, or notification service must be justified by production evidence and documented separately.
