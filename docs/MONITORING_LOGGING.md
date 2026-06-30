# Monitoring and Logging

HibeRota production operasyonu JSON log, sınırlı Docker log retention, host logrotate ve temel alarm sinyalleriyle başlar.

## Logging

- Django logları `apps.core.logging.JsonLogFormatter` ile JSON satırları olarak stdout'a yazılır.
- Docker Compose servisleri `json-file` driver için `max-size=10m`, `max-file=5` kullanır.
- Host üzerinde `/var/log/hiberota/*.log` için referans logrotate dosyası: `ops/logrotate/hiberota`.
- Secret, token, tam e-posta ve contact body loglanmaz.

## Monitoring

Referans health/alarm scripti:

```sh
MONITOR_SITE_URL=https://hiberota.com \
BACKUP_OUTPUT_DIR=/secure/backups \
ALERT_WEBHOOK_URL=... \
ops/monitoring/monitor-health.sh
```

`ALERT_WEBHOOK_URL` runtime secret olarak verilir; repoya yazılmaz.

Kontrol edilen başlangıç sinyalleri:

- `/health/live`
- `/health/ready`
- disk kullanımı
- exited Docker Compose servisleri
- son şifreli backup yaşı

Alarm sözleşmesi `ops/monitoring/alerts.json` içinde tutulur.

## Cron önerisi

```cron
*/5 * * * * /srv/hiberota/ops/monitoring/monitor-health.sh
```

## Eksikler

TLS expiry, queue age, kaynak başarısızlık oranı ve admin brute-force spike alarmları için bu görevde yalnızca alarm sözleşmesi eklendi. Gerçek metrik backend'i seçildiğinde bu sinyaller aynı ID'lerle bağlanır.
