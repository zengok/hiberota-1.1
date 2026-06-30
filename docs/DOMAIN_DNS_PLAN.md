# Domain and DNS Plan

Plan date: 2026-06-25

This plan defines the staging and production domain/DNS baseline. It does not perform a deploy, create DNS records, or include real server IP addresses or secrets.

## Current Nameserver State

As of the latest registrar screenshot, `hiberota.com` uses Güzel Hosting custom nameservers:

- `tr.guzelhosting.com`
- `eu.guzelhosting.com`
- `us.guzelhosting.com`
- `sg.guzelhosting.com`

DNS records must therefore be created in the Güzel Hosting DNS panel unless the domain is later migrated to Cloudflare nameservers.

## Domain Roles

| Environment | Hostname | Purpose | Indexing | Access |
|---|---|---|---|---|
| Production apex | `hiberota.com` | Canonical public website | Allowed after launch | Public |
| Production www | `www.hiberota.com` | Redirect to apex | Redirect only | Public |
| Staging | `staging.hiberota.com` | Pre-production validation | `noindex` | Cloudflare Access or equivalent gate |
| Admin policy | Same host, `/admin/` path | Staff-only Django admin | Not indexed | Staff auth, 2FA, rate limit |

If the final commercial domain changes, update this file and `DJANGO_ALLOWED_HOSTS`/CSRF origins before deployment.

## DNS Records

Current authoritative DNS: Güzel Hosting.

Cloudflare remains a planned CDN/WAF layer, but it is not the authoritative DNS provider while the nameservers above are active.

| Name | Type | Target | Proxy | Notes |
|---|---|---|---|---|
| `@` / `hiberota.com` | `A` or `AAAA` | Production origin IP placeholder | DNS only in Güzel Hosting | Primary canonical host. |
| `www` | `CNAME` | `hiberota.com` | DNS only in Güzel Hosting | Redirect to apex in Nginx/Django. |
| `staging` | `A` or `AAAA` | Staging origin IP placeholder | DNS only in Güzel Hosting | Separate staging server or isolated staging stack. |

Do not publish PostgreSQL or Redis DNS records. Ports `5432` and `6379` must not be internet-accessible.

## Cloudflare Baseline

- If Cloudflare is adopted later, change registrar nameservers to Cloudflare-provided nameservers first.
- DNS proxy enabled for public and staging web hosts after Cloudflare nameserver migration.
- SSL/TLS mode: Full (Strict).
- Always Use HTTPS enabled after origin TLS is valid.
- Managed WAF enabled.
- Bot and DDoS protection enabled.
- Static asset cache rules may target `/static/*`.
- Do not cache admin, contact, newsletter, survey, API, or authenticated/staff responses.
- Cloudflare Access or equivalent gate required for `staging.hiberota.com`.
- Rate limits required for `/admin/`, `/contact`, `/newsletter`, `/survey`, and `/api` before public launch.

## Origin and Nginx Requirements

- Origin accepts HTTP/HTTPS traffic only from Cloudflare IP ranges after DNS cutover.
- SSH is restricted to approved admin IP, VPN, or bastion.
- Nginx serves only `/static/` and controlled `/media/` aliases.
- Project root, `.git`, `.env`, logs, backups, dumps, source code, and config files are never web roots.
- `www.hiberota.com` redirects permanently to `https://hiberota.com`.
- Staging must emit `X-Robots-Tag: noindex, nofollow` or equivalent template/meta behavior.

## Django Environment Values

Production placeholders:

```text
DJANGO_ALLOWED_HOSTS=hiberota.com,www.hiberota.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://hiberota.com,https://www.hiberota.com
DJANGO_DEBUG=false
DJANGO_SECURE_SSL_REDIRECT=true
```

Staging placeholders:

```text
DJANGO_SETTINGS_MODULE=config.settings.staging
DJANGO_ALLOWED_HOSTS=staging.hiberota.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://staging.hiberota.com
DJANGO_DEBUG=false
DJANGO_SECURE_SSL_REDIRECT=true
SITE_BASE_URL=https://staging.hiberota.com
STAGING_ROBOTS_NOINDEX=true
```

All secret values remain outside the repository.

Use `.env.staging.example` as the staging environment template. Copy it to `.env` only on the staging host or CI secret workspace, then replace placeholder values from the secret manager.

## Launch Verification Checklist

Before production DNS cutover:

- Güzel Hosting DNS contains the staging `A`/`AAAA` record with the real staging origin IP.
- Staging deploy passes CI, migrations, smoke tests, and healthchecks.
- `https://staging.hiberota.com/health/live` is reachable behind the access gate.
- Staging has `noindex` behavior.
- Production origin TLS is valid.
- Cloudflare Full (Strict) works without certificate errors.
- `https://hiberota.com/health/live` returns healthy after cutover.
- `https://www.hiberota.com` redirects to `https://hiberota.com`.
- PostgreSQL and Redis are not reachable from the public internet.
- Admin login has 2FA and rate limiting before launch.
- Backup and restore plan is confirmed before production traffic.

## Open Items

- Final origin IP addresses are not defined in the repository.
- Staging `A`/`AAAA` target must be supplied by the hosting/server provider.
- Exact DNS TTL values should be chosen during cutover planning.
- Cloudflare nameserver migration is optional and not yet performed.
- Email sending domain records are intentionally out of scope until provider selection.
- Search Console, Bing Webmaster, AdSense, and analytics verification records are handled in later SEO/ads tasks.
