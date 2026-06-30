from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = ROOT / "ops/security/asvs-l1-checklist.json"


def test_asvs_l1_checklist_is_versioned_and_scoped() -> None:
    checklist = json.loads(CHECKLIST_PATH.read_text())

    assert checklist["standard"] == "OWASP ASVS"
    assert checklist["version"] == "5.0.0"
    assert checklist["verification_level"] == "L1"
    assert "staff-only admin" in checklist["scope"]
    assert checklist["source"].startswith("https://owasp.org/")


def test_asvs_l1_checklist_covers_required_hiberota_security_domains() -> None:
    checklist = json.loads(CHECKLIST_PATH.read_text())
    control_ids = {control["id"] for control in checklist["controls"]}

    expected = {
        "architecture-threat-model",
        "authentication-admin-only",
        "session-management",
        "access-control-admin",
        "input-validation-and-output-encoding",
        "cryptography-and-secrets",
        "error-handling-and-logging",
        "data-protection-and-privacy",
        "communications-security",
        "security-configuration",
        "file-and-resource-handling",
        "ssrf-and-outbound-requests",
        "dependency-and-supply-chain",
        "backup-and-recovery",
    }
    assert expected <= control_ids


def test_asvs_l1_checklist_has_evidence_and_next_actions_for_every_control() -> None:
    checklist = json.loads(CHECKLIST_PATH.read_text())
    valid_statuses = set(checklist["status_values"])

    for control in checklist["controls"]:
        assert control["status"] in valid_statuses
        assert control["evidence"]
        assert control["next_action"]


def test_asvs_document_keeps_partial_launch_gates_visible() -> None:
    document = (ROOT / "docs/OWASP_ASVS_L1_CHECKLIST.md").read_text()

    assert "Launch Gate" in document
    assert "partial" in document
    assert "Container image scan" in document
    assert "tam güvenli" in document
