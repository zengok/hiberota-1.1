from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "ops/cloudflare/waf-rate-limit-rules.json"


def test_cloudflare_security_rules_are_parseable_and_secret_free() -> None:
    payload = RULES_PATH.read_text()
    rules = json.loads(payload)

    assert rules["zone_settings"]["ssl_tls_mode"] == "full_strict"
    assert rules["zone_settings"]["dns_proxy"] == "enabled"
    assert "api_token" not in payload.lower()
    assert "zone_id" not in payload.lower()
    assert "account_id" not in payload.lower()
    assert "origin_ip" not in payload.lower()


def test_cloudflare_managed_protections_cover_waf_bots_and_ddos() -> None:
    rules = json.loads(RULES_PATH.read_text())
    names = {item["name"] for item in rules["managed_protections"]}

    assert "Cloudflare Managed Ruleset" in names
    assert "Cloudflare OWASP Core Ruleset" in names
    assert "HTTP DDoS Managed Ruleset" in names
    assert "Bot Fight Mode or equivalent bot protection" in names


def test_cloudflare_rate_limits_cover_sensitive_public_surfaces() -> None:
    rules = json.loads(RULES_PATH.read_text())
    rate_limits = {item["id"]: item for item in rules["rate_limits"]}

    expected_ids = {
        "global-public-soft-limit",
        "admin-login-limit",
        "contact-post-limit",
        "newsletter-post-limit",
        "survey-post-limit",
        "api-public-limit",
    }
    assert expected_ids <= set(rate_limits)

    assert rate_limits["admin-login-limit"]["requests"] <= 20
    assert rate_limits["contact-post-limit"]["period_seconds"] == 600
    assert rate_limits["api-public-limit"]["requests"] <= 120
    assert all(item["action"] == "managed_challenge" for item in rate_limits.values())


def test_cloudflare_rules_block_sensitive_files_and_bypass_dynamic_cache() -> None:
    rules = json.loads(RULES_PATH.read_text())
    waf_rules = {item["id"]: item for item in rules["custom_waf_rules"]}
    cache_rules = {item["id"]: item for item in rules["cache_rules"]}
    sensitive_expression = waf_rules["block-sensitive-files"]["expression"]

    assert waf_rules["block-sensitive-files"]["action"] == "block"
    assert "\\\\.env" in sensitive_expression
    assert "\\\\.git" in sensitive_expression
    assert "sql|sqlite|db" in sensitive_expression
    assert cache_rules["cache-static-assets"]["cache_eligibility"] == "eligible"
    assert cache_rules["bypass-dynamic-and-health"]["cache_eligibility"] == "bypass"
