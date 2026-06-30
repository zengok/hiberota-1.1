# Güzel Hosting DNS Checklist

`hiberota.com` currently uses Güzel Hosting nameservers:

- `tr.guzelhosting.com`
- `eu.guzelhosting.com`
- `us.guzelhosting.com`
- `sg.guzelhosting.com`

Use the Güzel Hosting DNS panel for records until nameservers are intentionally moved to another DNS provider.

## Staging Records

Create these after the staging server public IP is available:

| Host | Type | Value | TTL |
|---|---|---|---|
| `staging` | `A` | Staging server IPv4 | 300 during setup |
| `staging` | `AAAA` | Staging server IPv6, if provided | 300 during setup |

After DNS resolves, configure host-level TLS and proxying with
`docs/STAGING_SSL_NGINX.md`. `staging.hiberota.com` must not serve an old
static frontend or a certificate for another hostname.

Expected result:

```bash
dig +short NS hiberota.com
dig +short A staging.hiberota.com
curl -I https://staging.hiberota.com/health/live
python manage.py verify_staging_smoke
```

The staging HTTP response must include:

```text
X-Robots-Tag: noindex, nofollow
```

The smoke command must pass before source catalog import. It fails when
`staging.hiberota.com` is serving a static/old frontend, a non-JSON health
response, a missing staging noindex header, or production canonical URLs.

## Production Records

Create these only when production origin is ready:

| Host | Type | Value | TTL |
|---|---|---|---|
| `@` | `A` | Production server IPv4 | 300 during cutover |
| `@` | `AAAA` | Production server IPv6, if provided | 300 during cutover |
| `www` | `CNAME` | `hiberota.com` | 300 during cutover |

After cutover:

```bash
dig +short A hiberota.com
curl -I https://hiberota.com/health/live
curl -I https://www.hiberota.com
```

`www.hiberota.com` must redirect permanently to `https://hiberota.com`.

## Do Not Publish

Do not create public DNS records for:

- PostgreSQL,
- Redis,
- internal Docker service names,
- backup storage,
- admin-only private hostnames unless access is gated separately.
