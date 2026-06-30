#!/usr/bin/env sh
set -eu

site_url="${MONITOR_SITE_URL:-http://localhost:8080}"
disk_path="${MONITOR_DISK_PATH:-/}"
disk_max_percent="${MONITOR_DISK_MAX_PERCENT:-80}"
backup_root="${BACKUP_OUTPUT_DIR:-backups}"
backup_max_age_hours="${MONITOR_BACKUP_MAX_AGE_HOURS:-26}"

send_alert() {
    message="$1"
    printf '%s\n' "${message}" >&2
    if [ -n "${ALERT_WEBHOOK_URL:-}" ]; then
        escaped="$(printf '%s' "${message}" | sed 's/\\/\\\\/g; s/"/\\"/g')"
        curl -fsS -X POST -H 'Content-Type: application/json' \
            --data "{\"text\":\"${escaped}\"}" \
            "${ALERT_WEBHOOK_URL}" >/dev/null
    fi
}

failures=0

if ! curl -fsS "${site_url}/health/live" >/dev/null; then
    send_alert "hiberota alarm: live healthcheck failed for ${site_url}"
    failures=$((failures + 1))
fi

if ! curl -fsS "${site_url}/health/ready" >/dev/null; then
    send_alert "hiberota alarm: ready healthcheck failed for ${site_url}"
    failures=$((failures + 1))
fi

disk_used_percent="$(df -P "${disk_path}" | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
if [ "${disk_used_percent}" -ge "${disk_max_percent}" ]; then
    send_alert "hiberota alarm: disk usage ${disk_used_percent}% on ${disk_path}"
    failures=$((failures + 1))
fi

if command -v docker >/dev/null 2>&1 && docker compose ps --status=exited --format '{{.Name}}' | grep -q .; then
    send_alert "hiberota alarm: one or more compose services exited"
    failures=$((failures + 1))
fi

if [ -d "${backup_root}" ]; then
    if ! find "${backup_root}" -type f -name '*.tar.gz.enc' -mmin "-$((backup_max_age_hours * 60))" | grep -q .; then
        send_alert "hiberota alarm: no recent encrypted backup in ${backup_root}"
        failures=$((failures + 1))
    fi
else
    send_alert "hiberota alarm: backup root missing: ${backup_root}"
    failures=$((failures + 1))
fi

exit "${failures}"
