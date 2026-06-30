from __future__ import annotations

from pathlib import Path

from django.test import Client, override_settings

ROOT = Path(__file__).resolve().parents[1]


def test_staging_env_example_targets_hiberota_staging_domain() -> None:
    env_example = (ROOT / ".env.staging.example").read_text()

    assert "DJANGO_SETTINGS_MODULE=config.settings.staging" in env_example
    assert "DJANGO_ALLOWED_HOSTS=staging.hiberota.com" in env_example
    assert "DJANGO_CSRF_TRUSTED_ORIGINS=https://staging.hiberota.com" in env_example
    assert "SITE_BASE_URL=https://staging.hiberota.com" in env_example
    assert "ADSENSE_ENABLED=false" in env_example
    assert "STAGING_ROBOTS_NOINDEX=true" in env_example
    assert "EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend" in env_example
    assert "DEFAULT_FROM_EMAIL=no-reply@hiberota.com" in env_example
    assert "EMAIL_HOST_PASSWORD=replace-with-staging-smtp-password" in env_example


def test_staging_env_example_is_allowed_by_gitignore() -> None:
    gitignore = (ROOT / ".gitignore").read_text()

    assert "!.env.staging.example" in gitignore


@override_settings(STAGING_ROBOTS_NOINDEX=True)
def test_staging_noindex_header_is_emitted() -> None:
    response = Client().get("/health/live")

    assert response.headers["X-Robots-Tag"] == "noindex, nofollow"
