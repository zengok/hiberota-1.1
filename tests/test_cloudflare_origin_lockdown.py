from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cloudflare_nginx_template_restricts_origin_and_trusts_cf_header() -> None:
    template = (ROOT / "nginx/default.cloudflare.conf").read_text()

    assert "include /etc/nginx/cloudflare/cloudflare-real-ip.conf;" in template
    assert "include /etc/nginx/cloudflare/cloudflare-origin-allow.conf;" in template
    assert "proxy_set_header X-Real-IP $realip_remote_addr;" in template
    assert "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;" in template


def test_cloudflare_allowlist_generator_uses_official_sources_without_embedded_ranges() -> None:
    script = (ROOT / "ops/cloudflare/generate-nginx-cloudflare-allowlist.sh").read_text()

    assert "https://www.cloudflare.com/ips-v4" in script
    assert "https://www.cloudflare.com/ips-v6" in script
    assert "set_real_ip_from ${cidr};" in script
    assert "real_ip_header CF-Connecting-IP;" in script
    assert "allow ${cidr};" in script
    assert "deny all;" in script


def test_firewalld_lockdown_script_limits_http_https_to_cloudflare_ranges() -> None:
    script = (ROOT / "ops/firewalld/cloudflare-origin-lockdown.sh").read_text()

    assert "https://www.cloudflare.com/ips-v4" in script
    assert "https://www.cloudflare.com/ips-v6" in script
    assert "--remove-service=http" in script
    assert "--remove-service=https" in script
    assert 'port port=\\"80\\" protocol=\\"tcp\\" accept' in script
    assert 'port port=\\"443\\" protocol=\\"tcp\\" accept' in script
    assert "firewall-cmd --reload" in script
