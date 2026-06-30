#!/usr/bin/env sh
# ============================================================
# HibeRota — Production Deploy Script
# Kullanım: sh ops/deploy.sh
# ============================================================
set -eu

REMOTE_USER="${REMOTE_USER:-deploy}"
REMOTE_HOST="70.40.138.74"
REMOTE_DIR="${REMOTE_DIR:-/opt/hiberota}"
REMOTE_UPLOAD_DIR="${REMOTE_UPLOAD_DIR:-/home/deploy/hiberota-upload-current}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/hiberota_deploy_ed25519}"

LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Kodlar sunucuya gönderiliyor: ${REMOTE_HOST}:${REMOTE_UPLOAD_DIR}"
rsync -avz --delete \
  --exclude '.venv' \
  --exclude '.git' \
  --exclude '.github' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude 'staticfiles' \
  --exclude 'media' \
  --exclude '.test-db.sqlite3' \
  --exclude '.env' \
  --exclude '*.pyc' \
  -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
  "${LOCAL_DIR}/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_UPLOAD_DIR}/"

echo "==> Sunucuda scheduler env ayarları güncelleniyor ve containerlar yeniden başlatılıyor..."
ssh -i "${SSH_KEY}" "${REMOTE_USER}@${REMOTE_HOST}" "
  set -e
  sudo rsync -a --delete \
    --exclude '.env' \
    --exclude 'media' \
    --exclude 'staticfiles' \
    --exclude 'deploy-backups' \
    ${REMOTE_UPLOAD_DIR}/ ${REMOTE_DIR}/

  cd ${REMOTE_DIR}

  echo '--- .env scheduler ayarları düzeltiliyor ---'
  sudo sed -i 's/^SOURCE_SCHEDULER_ENABLED=.*/SOURCE_SCHEDULER_ENABLED=true/' .env
  sudo sed -i 's/^SOURCE_SCHEDULER_ROLLBACK_PAUSED=.*/SOURCE_SCHEDULER_ROLLBACK_PAUSED=false/' .env
  sudo sed -i 's/^SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=.*/SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=false/' .env
  sudo sed -i 's/^SOURCE_SCHEDULER_MAX_DUE_SOURCES=.*/SOURCE_SCHEDULER_MAX_DUE_SOURCES=10/' .env
  sudo sed -i 's/^SOURCE_SCHEDULER_DEGRADE_AFTER_FAILURES=.*/SOURCE_SCHEDULER_DEGRADE_AFTER_FAILURES=3/' .env

  # Eğer bu satırlar .env'de yoksa ekle
  sudo sh -c \"grep -q '^SOURCE_SCHEDULER_ENABLED=' .env || echo 'SOURCE_SCHEDULER_ENABLED=true' >> .env\"
  sudo sh -c \"grep -q '^SOURCE_SCHEDULER_ROLLBACK_PAUSED=' .env || echo 'SOURCE_SCHEDULER_ROLLBACK_PAUSED=false' >> .env\"
  sudo sh -c \"grep -q '^SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=' .env || echo 'SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=false' >> .env\"
  sudo sh -c \"grep -q '^SOURCE_SCHEDULER_MAX_DUE_SOURCES=' .env || echo 'SOURCE_SCHEDULER_MAX_DUE_SOURCES=10' >> .env\"
  sudo sh -c \"grep -q '^SOURCE_SCHEDULER_DEGRADE_AFTER_FAILURES=' .env || echo 'SOURCE_SCHEDULER_DEGRADE_AFTER_FAILURES=3' >> .env\"

  echo '--- Mevcut .env scheduler satırları ---'
  sudo grep 'SOURCE_SCHEDULER' .env

  echo '--- Docker image yeniden inşa ediliyor ---'
  sudo docker compose build --no-cache web celery_worker celery_beat

  echo '--- Servisler yeniden başlatılıyor ---'
  sudo docker compose up -d --remove-orphans web celery_worker celery_beat nginx
  sudo docker compose restart nginx

  echo '--- 15 saniye bekleniyor (container başlangıcı) ---'
  sleep 15

  echo '--- Servis durumu ---'
  sudo docker compose ps

  echo '--- Healthcheck ---'
  curl -fsS -H 'Host: hiberota.com' http://127.0.0.1:8080/health/live
  curl -fsS -H 'Host: hiberota.com' http://127.0.0.1:8080/health/ready

  echo '--- Web container logları (entrypoint çıktısı) ---'
  sudo docker compose logs --tail=50 web

  echo '--- Celery beat logları ---'
  sudo docker compose logs --tail=20 celery_beat

  echo '--- Source catalog import sonucu ---'
  sudo docker compose exec -T web python manage.py import_source_catalog data/source_catalog_import.csv --commit 2>&1 | tail -5 || true
"

echo ""
echo "✅ Deploy tamamlandı!"
echo "   Site: https://hiberota.com"
echo "   Scheduler 5 dakika içinde ilk crawl'ı başlatacak."
