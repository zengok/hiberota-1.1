from __future__ import annotations

import json
import logging
from pathlib import Path

from apps.core.logging import JsonLogFormatter

ROOT = Path(__file__).resolve().parents[1]


def test_json_log_formatter_outputs_structured_safe_fields() -> None:
    record = logging.LogRecord("hiberota.test", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "hiberota.test"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_docker_compose_uses_json_file_log_rotation_for_services() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "driver: json-file" in compose
    assert 'max-size: "10m"' in compose
    assert 'max-file: "5"' in compose
    assert "logging: *default-logging" in compose


def test_monitoring_script_checks_health_disk_containers_and_backup_age() -> None:
    script = (ROOT / "ops/monitoring/monitor-health.sh").read_text()

    assert "/health/live" in script
    assert "/health/ready" in script
    assert "MONITOR_DISK_MAX_PERCENT" in script
    assert "docker compose ps --status=exited" in script
    assert "MONITOR_BACKUP_MAX_AGE_HOURS" in script
    assert "ALERT_WEBHOOK_URL" in script


def test_alert_catalog_covers_required_initial_signals() -> None:
    alerts = json.loads((ROOT / "ops/monitoring/alerts.json").read_text())
    alert_ids = {item["id"] for item in alerts["alerts"]}

    assert "site-unavailable" in alert_ids
    assert "db-or-cache-unavailable" in alert_ids
    assert "storage-usage-high" in alert_ids
    assert "container-exited" in alert_ids
    assert "backup-stale" in alert_ids
    assert "admin-brute-force" in alert_ids
    assert "ssl-expiry" in alert_ids


def test_logrotate_policy_exists_for_host_logs() -> None:
    logrotate = (ROOT / "ops/logrotate/hiberota").read_text()

    assert "/var/log/hiberota/*.log" in logrotate
    assert "daily" in logrotate
    assert "rotate 14" in logrotate
    assert "compress" in logrotate
