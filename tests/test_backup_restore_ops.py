from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_backup_script_creates_encrypted_pg_dump_and_checksum() -> None:
    script = (ROOT / "ops/backup/create-encrypted-backup.sh").read_text()

    assert "BACKUP_ENCRYPTION_PASSPHRASE" in script
    assert "pg_dump" in script
    assert "--format=custom" in script
    assert "openssl enc -aes-256-cbc -pbkdf2 -salt" in script
    assert "shasum -a 256" in script
    assert "media.tar.gz" in script


def test_verify_script_checks_checksum_database_dump_and_media_archive() -> None:
    script = (ROOT / "ops/backup/verify-encrypted-backup.sh").read_text()

    assert "shasum -a 256 -c" in script
    assert "openssl enc -d -aes-256-cbc -pbkdf2" in script
    assert "pg_restore --list" in script
    assert "tar -tzf" in script
    assert "manifest.txt" in script


def test_restore_test_script_targets_separate_restore_database() -> None:
    script = (ROOT / "ops/backup/restore-test.sh").read_text()

    assert "RESTORE_POSTGRES_DB" in script
    assert "RESTORE_POSTGRES_PASSWORD" in script
    assert "pg_restore" in script
    assert "--clean" in script
    assert "--if-exists" in script
    assert "SELECT 1;" in script


def test_backup_restore_document_keeps_real_secrets_out_of_repo() -> None:
    document = (ROOT / "docs/BACKUP_RESTORE.md").read_text()

    assert "production DB üzerinde çalıştırılmaz" in document
    assert "repoya yazılmaz" in document
    assert "Aylık restore testi" in document
