#!/usr/bin/env sh
set -eu

required_vars="POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD POSTGRES_HOST POSTGRES_PORT BACKUP_ENCRYPTION_PASSPHRASE"
for var_name in ${required_vars}; do
    eval "var_value=\${${var_name}:-}"
    if [ -z "${var_value}" ]; then
        echo "Missing required environment variable: ${var_name}" >&2
        exit 1
    fi
done

backup_root="${BACKUP_OUTPUT_DIR:-backups}"
media_root="${MEDIA_ROOT:-media}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_name="hiberota-${timestamp}"
work_dir="$(mktemp -d)"
output_dir="${backup_root}/${timestamp}"

cleanup() {
    rm -rf "${work_dir}"
}
trap cleanup EXIT

mkdir -p "${output_dir}"

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    --format=custom \
    --no-owner \
    --no-acl \
    --host="${POSTGRES_HOST}" \
    --port="${POSTGRES_PORT}" \
    --username="${POSTGRES_USER}" \
    --dbname="${POSTGRES_DB}" \
    --file="${work_dir}/database.dump"

if [ -d "${media_root}" ]; then
    tar -C "${media_root}" -czf "${work_dir}/media.tar.gz" .
else
    tar -czf "${work_dir}/media.tar.gz" --files-from /dev/null
fi

cat > "${work_dir}/manifest.txt" <<EOF
backup_name=${backup_name}
created_at_utc=${timestamp}
database=${POSTGRES_DB}
media_archive=media.tar.gz
database_archive=database.dump
format=tar.gz.openssl-aes-256-cbc-pbkdf2
EOF

tar -C "${work_dir}" -czf - manifest.txt database.dump media.tar.gz \
    | openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_ENCRYPTION_PASSPHRASE \
    > "${output_dir}/${backup_name}.tar.gz.enc"

shasum -a 256 "${output_dir}/${backup_name}.tar.gz.enc" > "${output_dir}/${backup_name}.tar.gz.enc.sha256"

printf '%s\n' "${output_dir}/${backup_name}.tar.gz.enc"
printf '%s\n' "${output_dir}/${backup_name}.tar.gz.enc.sha256"
