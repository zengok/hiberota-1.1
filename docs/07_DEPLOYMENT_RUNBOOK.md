# Deployment ve Operasyon Runbook

## 1. Hedef altyapı

- AlmaLinux 9
- 4 vCPU
- 4 GB RAM
- 60 GB disk
- 2 TB trafik
- hiberota.com
- Cloudflare proxy
- Docker Compose

SLA sağlayıcı seviyesi ayrıca doğrulanmalıdır.

## 2. Ortam ayrımı

### Local

- Docker Compose
- dummy e-posta backend veya sandbox
- debug toolbar opsiyonel
- gerçek production verisi yok

### Staging

- ayrı subdomain
- `noindex`
- basic access/Cloudflare Access
- ayrı DB ve secret
- production'a yakın compose
- test e-posta recipient allowlist
- reklam kapalı

### Production

- sadece onaylı image/tag
- immutable release
- DEBUG off
- backup
- monitoring
- Cloudflare strict TLS
- admin 2FA

## 3. Containerlar

- `web`
- `worker`
- `beat`
- `postgres`
- `redis`
- `nginx`
- opsiyonel `backup`
- opsiyonel, yalnızca görev anında `headless-worker`

Her serviste healthcheck, restart policy ve resource limit bulunur.

## 4. Deploy sırası

1. CI test/security/build.
2. Image tag commit SHA ile üret.
3. Staging deploy.
4. Migration planını kontrol et.
5. Staging smoke.
6. Backup al.
7. Production image pull.
8. Gerekirse backward-compatible migration.
9. Web/worker/beat kontrollü restart.
10. Healthcheck.
11. Public smoke.
12. Queue ve error log kontrolü.
13. Release kaydı.

## 5. Migration ilkeleri

- Büyük tablo migrationları iki aşamalı.
- Önce nullable kolon/indeks concurrent yaklaşımı.
- Backfill ayrı task.
- Sonra constraint.
- Deploy ile uzun bloklayan migration yok.
- Rollback mümkün olmayan migration öncesi backup ve runbook.
- Eski worker ile yeni schema geçici olarak uyumlu olmalı.

## 6. Backup

Minimum:

- günlük `pg_dump` custom format,
- haftalık doğrulanmış uzak kopya,
- medya backup,
- env/secret backup ayrı güvenli sistemde,
- 7 günlük kısa, 4 haftalık, 6 aylık örnek retention,
- aylık restore test.

Kesin retention kapasite ve hukuk gereksinimine göre ayarlanır.

## 7. Monitoring

### Sistem

- CPU
- RAM/swap
- disk ve inode
- container restart
- network
- TLS expiry

### Uygulama

- 5xx/4xx
- latency
- request rate
- DB connection
- slow query
- cache hit
- queue depth
- task failure
- crawl success
- 403/429 source oranı
- email bounce/complaint
- backup sonucu

### Alarm

- site unavailable
- DB unavailable
- disk > 80%
- queue age threshold
- source failure threshold
- backup failure
- admin brute force
- sudden 404/403 spike
- SSL expiry

## 8. Log politikası

- JSON structured logs.
- request ID/correlation ID.
- Secret ve token loglanmaz.
- E-posta tam değeri loglanmaz; gerekirse maskeli.
- Contact body loglanmaz.
- Source response body varsayılan loglanmaz.
- Rotation.
- UTC timestamp.
- Admin audit ayrı.
- Production log seviyesi kontrollü.

## 9. Rollback

Uygulama:

- önceki image tag'e dön,
- backward-compatible schema,
- worker/beat versiyonunu birlikte yönet,
- cache temizleme gerekiyorsa kontrollü.

Veri:

- otomatik destructive rollback yok,
- restore yalnızca olay komutanı/onay ile,
- yanlış crawl publish için batch unpublish/revert aracı.

## 10. Olay müdahalesi

1. Algıla.
2. Etkiyi sınıflandır.
3. Gerekirse source/scheduler/publish'i durdur.
4. Kanıtı koru.
5. Secret rotate.
6. Hizmeti güvenli moda al.
7. Kök neden.
8. Düzeltme.
9. Restore/doğrulama.
10. Postmortem ve aksiyon.

Public güvenlik olayı iletişimi hukuk ve yönetim onayıyla yapılır.
