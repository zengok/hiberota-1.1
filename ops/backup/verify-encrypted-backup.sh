#!/usr/bin/env sh
set -eu

backup_file="${1:-}"
if [ -z "${backup_file}" ]; then
    echo "Usage: $0 /path/to/hiberota-backup.tar.gz.enc" >&2
    exit 1
fi

if [ -z "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]; then
    echo "Missing required environment variable: BACKUP_ENCRYPTION_PASSPHRASE" >&2
    exit 1
fi

checksum_file="${backup_file}.sha256"
if [ -f "${checksum_file}" ]; then
    shasum -a 256 -c "${checksum_file}"
fi

work_dir="$(mktemp -d)"
cleanup() {
    rm -rf "${work_dir}"
}
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_PASSPHRASE -in "${backup_file}" \
    | tar -C "${work_dir}" -xzf -

test -s "${work_dir}/manifest.txt"
test -s "${work_dir}/database.dump"
test -s "${work_dir}/media.tar.gz"

pg_restore --list "${work_dir}/database.dump" >/dev/null
tar -tzf "${work_dir}/media.tar.gz" >/dev/null

cat "${work_dir}/manifest.txt"
