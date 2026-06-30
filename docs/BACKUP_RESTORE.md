# Backup Restore

Bu görev production backup çalıştırmaz. Repo, PostgreSQL ve medya yedekleri için şifreli backup ve restore test iskeletini sağlar.

## Kapsam

- PostgreSQL logical backup: `pg_dump --format=custom`
- Medya backup: `media.tar.gz`
- Manifest: UTC zaman, veritabanı adı ve arşiv bileşenleri
- Şifreleme: OpenSSL `aes-256-cbc` + `pbkdf2`, passphrase yalnızca runtime env üzerinden
- Bütünlük: SHA-256 checksum
- Restore testi: `pg_restore --list`, medya arşiv listeleme ve opsiyonel test veritabanına restore

## Secret kuralı

`BACKUP_ENCRYPTION_PASSPHRASE`, PostgreSQL parolaları, uzak bucket credential bilgileri ve gerçek backup konumu repoya yazılmaz.

## Backup

```sh
POSTGRES_DB=hiberota \
POSTGRES_USER=hiberota \
POSTGRES_PASSWORD=... \
POSTGRES_HOST=postgres \
POSTGRES_PORT=5432 \
BACKUP_ENCRYPTION_PASSPHRASE=... \
BACKUP_OUTPUT_DIR=/secure/backups \
MEDIA_ROOT=/app/media \
ops/backup/create-encrypted-backup.sh
```

## Arşiv doğrulama

```sh
BACKUP_ENCRYPTION_PASSPHRASE=... \
ops/backup/verify-encrypted-backup.sh /secure/backups/<timestamp>/hiberota-<timestamp>.tar.gz.enc
```

## Restore testi

Restore testi production DB üzerinde çalıştırılmaz. Ayrı staging/test veritabanı kullanılır.

```sh
BACKUP_ENCRYPTION_PASSPHRASE=... \
RESTORE_POSTGRES_DB=hiberota_restore_test \
RESTORE_POSTGRES_USER=hiberota_restore \
RESTORE_POSTGRES_PASSWORD=... \
RESTORE_POSTGRES_HOST=postgres \
RESTORE_POSTGRES_PORT=5432 \
ops/backup/restore-test.sh /secure/backups/<timestamp>/hiberota-<timestamp>.tar.gz.enc
```

## Retention

Başlangıç politikası:

- 7 günlük kısa yerel retention
- 4 haftalık haftalık uzak kopya
- 6 aylık aylık uzak kopya
- Aylık restore testi

Yerel kısa retention referans scripti:

```sh
BACKUP_OUTPUT_DIR=/secure/backups BACKUP_RETENTION_DAILY_DAYS=7 ops/backup/prune-local-backups.sh
```

Uzak kopya hedefi sağlayıcı ve hukuk gereksinimleri netleştiğinde eklenir. Uzak kopyalar şifreli arşiv olarak taşınır.

## Kabul

- Backup arşivi ve checksum üretilir.
- Arşiv passphrase olmadan açılamaz.
- `verify-encrypted-backup.sh` başarılıdır.
- Aylık `restore-test.sh` test veritabanında başarılıdır.
- Restore sonucu, tarih, arşiv adı ve süre operasyon kaydına işlenir.
