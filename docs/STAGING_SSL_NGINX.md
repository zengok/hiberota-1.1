# Staging SSL and Host Nginx Runbook

This runbook fixes the host-level `staging.hiberota.com` TLS and proxy path.
It does not contain SSH usernames, private keys, passwords, tokens, or real
secret values.

## Expected Topology

```text
internet
  -> host nginx :443 for staging.hiberota.com
  -> Docker Compose nginx on 127.0.0.1:8080
  -> web:8000 gunicorn/Django
```

The host Nginx vhost must not serve an old static frontend for
`staging.hiberota.com`. It must terminate a certificate valid for
`staging.hiberota.com` and proxy traffic to `127.0.0.1:8080`.

## Prerequisites

- `staging.hiberota.com` DNS resolves to the staging host.
- Docker Compose stack is running and exposes local Nginx on `127.0.0.1:8080`.
- `.env` on the staging host uses:
  - `DJANGO_SETTINGS_MODULE=config.settings.staging`
  - `DJANGO_ALLOWED_HOSTS=staging.hiberota.com`
  - `DJANGO_CSRF_TRUSTED_ORIGINS=https://staging.hiberota.com`
  - `SITE_BASE_URL=https://staging.hiberota.com`
- The old/static `staging.hiberota.com` Nginx server block is disabled.

## Host Nginx Vhost

Install the repository template on the host:

```bash
sudo install -m 0644 nginx/staging.host.conf /etc/nginx/conf.d/hiberota-staging.conf
```

The template expects certificates at:

```text
/etc/letsencrypt/live/staging.hiberota.com/fullchain.pem
/etc/letsencrypt/live/staging.hiberota.com/privkey.pem
```

## Certificate

Use the provider-approved ACME client flow for the host. With Certbot webroot,
the shape is:

```bash
sudo mkdir -p /var/www/certbot
sudo certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d staging.hiberota.com
```

If Certbot uses the Nginx plugin instead, keep the final vhost equivalent to
`nginx/staging.host.conf`: `server_name staging.hiberota.com`, valid
certificate paths, HTTPS redirect, and `proxy_pass http://127.0.0.1:8080`.

## Apply and Verify

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -I https://staging.hiberota.com/health/live
python manage.py verify_staging_smoke
```

Expected result:

- TLS validation succeeds for `staging.hiberota.com`.
- `/health/live` returns Django JSON: `{"status": "ok", "service": "hiberota"}`.
- Responses include `X-Robots-Tag: noindex, nofollow`.
- The homepage canonical points to `https://staging.hiberota.com/`.

## Rollback

If the vhost fails:

1. Restore the previous host Nginx config from the host backup.
2. Run `sudo nginx -t`.
3. Reload Nginx only after syntax passes.
4. Keep source catalog import blocked until `python manage.py verify_staging_smoke` passes.
