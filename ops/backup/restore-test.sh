#!/usr/bin/env sh
set -eu

backup_file="${1:-}"
if [ -z "${backup_file}" ]; then
    echo "Usage: $0 /path/to/hiberota-backup.tar.gz.enc" >&2
    exit 1
fi

required_vars="BACKUP_ENCRYPTION_PASSPHRASE RESTORE_POSTGRES_DB RESTORE_POSTGRES_USER RESTORE_POSTGRES_PASSWORD RESTORE_POSTGRES_HOST RESTORE_POSTGRES_PORT"
for var_name in ${required_vars}; do
    eval "var_value=\${${var_name}:-}"
    if [ -z "${var_value}" ]; then
        echo "Missing required environment variable: ${var_name}" >&2
        exit 1
    fi
done

work_dir="$(mktemp -d)"
cleanup() {
    rm -rf "${work_dir}"
}
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_PASSPHRASE -in "${backup_file}" \
    | tar -C "${work_dir}" -xzf -

pg_restore --list "${work_dir}/database.dump" >/dev/null

PGPASSWORD="${RESTORE_POSTGRES_PASSWORD}" pg_restore \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --host="${RESTORE_POSTGRES_HOST}" \
    --port="${RESTORE_POSTGRES_PORT}" \
    --username="${RESTORE_POSTGRES_USER}" \
    --dbname="${RESTORE_POSTGRES_DB}" \
    "${work_dir}/database.dump"

PGPASSWORD="${RESTORE_POSTGRES_PASSWORD}" psql \
    --host="${RESTORE_POSTGRES_HOST}" \
    --port="${RESTORE_POSTGRES_PORT}" \
    --username="${RESTORE_POSTGRES_USER}" \
    --dbname="${RESTORE_POSTGRES_DB}" \
    --command="SELECT 1;" >/dev/null

tar -tzf "${work_dir}/media.tar.gz" >/dev/null
cat "${work_dir}/manifest.txt"
