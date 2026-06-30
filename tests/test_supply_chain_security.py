from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_runs_python_and_container_security_scans() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()

    assert "pip-audit" in workflow
    assert "bandit -r apps config automation" in workflow
    assert "docker build -t hiberota:ci ." in workflow
    assert "aquasecurity/trivy-action@0.33.1" in workflow
    assert "severity: CRITICAL,HIGH" in workflow
    assert 'exit-code: "1"' in workflow


def test_dependency_review_blocks_high_risk_dependency_changes() -> None:
    workflow = (ROOT / ".github/workflows/dependency-review.yml").read_text()

    assert "actions/dependency-review-action@v4" in workflow
    assert "fail-on-severity: high" in workflow
    assert "deny-licenses: GPL-3.0, AGPL-3.0" in workflow


def test_dependabot_tracks_pip_docker_and_actions() -> None:
    dependabot = (ROOT / ".github/dependabot.yml").read_text()

    assert "package-ecosystem: pip" in dependabot
    assert "package-ecosystem: docker" in dependabot
    assert "package-ecosystem: github-actions" in dependabot
    assert "interval: weekly" in dependabot


def test_supply_chain_document_records_release_gate() -> None:
    document = (ROOT / "docs/SUPPLY_CHAIN_SECURITY.md").read_text()

    assert "Trivy container scan" in document
    assert "Dependency Review" in document
    assert "Yüksek veya kritik CVE" in document
    assert "registry credential" in document
