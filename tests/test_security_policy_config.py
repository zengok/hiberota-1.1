from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_security_policy_template_avoids_sensitive_operational_terms() -> None:
    template = (ROOT / "templates/pages/security_policy.html").read_text().lower()

    assert "firewall" not in template
    assert "origin ip" not in template
    assert "secret yönetimi" not in template
    assert "ddos" in template
    assert "kalıcılık" in template


def test_security_txt_contact_placeholder_is_documented_in_env_example() -> None:
    env_example = (ROOT / ".env.example").read_text()

    assert "SECURITY_CONTACT_EMAIL=security@example.invalid" in env_example
    assert "SECURITY_TXT_CONTACT=mailto:security@example.invalid" in env_example
