from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_call_list_template_has_no_inline_change_handler() -> None:
    template = (ROOT / "templates/pages/call_list.html").read_text()

    assert "onchange=" not in template
    assert "data-auto-submit" in template


def test_forms_script_binds_auto_submit_controls_without_inline_javascript() -> None:
    script = (ROOT / "static/js/forms.js").read_text()

    assert "[data-auto-submit]" in script
    assert 'addEventListener("change"' in script
    assert ".form?.submit()" in script


def test_security_headers_document_mentions_embed_exception_and_hsts_preload_gate() -> None:
    document = (ROOT / "docs/SECURITY_HEADERS.md").read_text()

    assert "Embed endpointleri" in document
    assert "DJANGO_SECURE_HSTS_PRELOAD" in document
    assert "Preload yalnızca subdomain kapsamı doğrulandıktan sonra açılır" in document


def test_staging_settings_disables_hsts_preload_and_enables_noindex() -> None:
    settings_file = (ROOT / "config/settings/staging.py").read_text()

    assert "STAGING_ROBOTS_NOINDEX" in settings_file
    assert "SECURE_HSTS_PRELOAD = False" in settings_file


def test_production_settings_trust_host_nginx_https_proxy_header() -> None:
    settings_file = (ROOT / "config/settings/production.py").read_text()
    compose_file = (ROOT / "docker-compose.yml").read_text()
    nginx_file = (ROOT / "nginx/default.conf").read_text()

    assert 'SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")' in settings_file
    assert "USE_X_FORWARDED_HOST = True" in settings_file
    assert "Host: hiberota.com" in compose_file
    assert "X-Forwarded-Proto: https" in compose_file
    assert "$http_x_forwarded_proto $hiberota_forwarded_proto" in nginx_file
    assert "proxy_set_header X-Forwarded-Proto $hiberota_forwarded_proto;" in nginx_file
