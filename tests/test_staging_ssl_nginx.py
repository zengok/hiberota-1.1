from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_staging_host_nginx_vhost_terminates_tls_and_proxies_to_compose() -> None:
    config = (ROOT / "nginx/staging.host.conf").read_text()

    assert "server_name staging.hiberota.com;" in config
    assert "listen 443 ssl http2;" in config
    assert "/etc/letsencrypt/live/staging.hiberota.com/fullchain.pem" in config
    assert "/etc/letsencrypt/live/staging.hiberota.com/privkey.pem" in config
    assert "proxy_pass http://127.0.0.1:8080;" in config
    assert "proxy_set_header X-Forwarded-Proto https;" in config
    assert 'add_header X-Robots-Tag "noindex, nofollow" always;' in config
    assert "location ~ /\\.(?!well-known)" in config
    assert "alias " not in config
    assert "root /srv" not in config


def test_staging_ssl_runbook_links_smoke_gate_and_old_static_blocker() -> None:
    runbook = (ROOT / "docs/STAGING_SSL_NGINX.md").read_text()

    assert "python manage.py verify_staging_smoke" in runbook
    assert "old static frontend" in runbook
    assert "proxy_pass http://127.0.0.1:8080" in runbook
    assert "Keep source catalog import blocked" in runbook
