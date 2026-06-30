from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_admin_security_environment_flags_are_documented() -> None:
    env_example = (ROOT / ".env.example").read_text()

    assert "ADMIN_TOTP_REQUIRED=true" in env_example
    assert "ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS=5" in env_example
    assert "ADMIN_LOGIN_RATE_LIMIT_LOCKOUT_SECONDS=900" in env_example


def test_admin_totp_model_does_not_expose_secret_in_admin_fields() -> None:
    admin_file = (ROOT / "apps/security/admin.py").read_text()

    assert "masked_secret_key" in admin_file
    assert '"secret_key"' not in admin_file
