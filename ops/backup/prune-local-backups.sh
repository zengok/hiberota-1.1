#!/usr/bin/env sh
set -eu

backup_root="${BACKUP_OUTPUT_DIR:-backups}"
daily_days="${BACKUP_RETENTION_DAILY_DAYS:-7}"

if [ ! -d "${backup_root}" ]; then
    exit 0
fi

find "${backup_root}" -type f -name '*.tar.gz.enc' -mtime "+${daily_days}" -print -delete
find "${backup_root}" -type f -name '*.tar.gz.enc.sha256' -mtime "+${daily_days}" -print -delete
find "${backup_root}" -type d -empty -print -delete
