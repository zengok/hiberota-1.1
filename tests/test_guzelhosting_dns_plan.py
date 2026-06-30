from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_domain_plan_records_current_guzelhosting_nameservers() -> None:
    plan = (ROOT / "docs/DOMAIN_DNS_PLAN.md").read_text()

    assert "tr.guzelhosting.com" in plan
    assert "eu.guzelhosting.com" in plan
    assert "us.guzelhosting.com" in plan
    assert "sg.guzelhosting.com" in plan
    assert "Current authoritative DNS: Güzel Hosting" in plan


def test_guzelhosting_dns_checklist_has_staging_and_production_records() -> None:
    checklist = (ROOT / "docs/GUZELHOSTING_DNS_CHECKLIST.md").read_text()

    assert "`staging` | `A`" in checklist
    assert "`@` | `A`" in checklist
    assert "`www` | `CNAME`" in checklist
    assert "X-Robots-Tag: noindex, nofollow" in checklist
