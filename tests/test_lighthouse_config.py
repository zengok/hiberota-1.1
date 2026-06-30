from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lighthouse_budget_file_tracks_core_web_vitals_targets() -> None:
    budget = json.loads((ROOT / "lighthouse-budget.json").read_text())

    assert budget[0]["path"] == "/*"
    timings = {item["metric"]: item["budget"] for item in budget[0]["timings"]}
    assert timings["largest-contentful-paint"] == 2500
    assert timings["cumulative-layout-shift"] == 0.1
    assert timings["total-blocking-time"] == 200

    resource_sizes = {item["resourceType"]: item["budget"] for item in budget[0]["resourceSizes"]}
    assert resource_sizes["total"] <= 900
    assert resource_sizes["script"] <= 220


def test_lighthouse_ci_config_covers_public_entry_pages() -> None:
    config = json.loads((ROOT / "lighthouserc.json").read_text())

    urls = set(config["ci"]["collect"]["url"])
    assert "http://127.0.0.1:8110/" in urls
    assert "http://127.0.0.1:8110/cagrilar/" in urls
    assert "http://127.0.0.1:8110/proje-rehberi/" in urls

    assertions = config["ci"]["assert"]["assertions"]
    assert assertions["largest-contentful-paint"] == ["warn", {"maxNumericValue": 2500}]
    assert assertions["cumulative-layout-shift"] == ["error", {"maxNumericValue": 0.1}]
    assert assertions["total-blocking-time"] == ["warn", {"maxNumericValue": 200}]
    assert assertions["categories:seo"] == ["error", {"minScore": 0.9}]


def test_lighthouse_workflow_runs_against_django_test_settings() -> None:
    workflow = (ROOT / ".github/workflows/lighthouse.yml").read_text()

    assert "@lhci/cli autorun --config=lighthouserc.json" in workflow
    assert "DJANGO_SETTINGS_MODULE: config.settings.test" in workflow
    assert 'HIBEROTA_TEST_SQLITE: "true"' in workflow
    assert 'ADSENSE_ENABLED: "false"' in workflow
    assert "python manage.py runserver 127.0.0.1:8110 --insecure" in workflow
