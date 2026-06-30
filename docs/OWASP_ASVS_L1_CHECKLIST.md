# OWASP ASVS L1 Checklist

Bu kontrol listesi HibeRota ilk ticari sürüm hazırlığı için OWASP ASVS Level 1 taban çizgisini izler.

- Standart: OWASP Application Security Verification Standard
- Sürüm: 5.0.0
- Kapsam: Django public hibe platformu ve staff-only admin
- Makine okunabilir liste: `ops/security/asvs-l1-checklist.json`
- Kaynak: https://owasp.org/www-project-application-security-verification-standard/

## Durum Anlamları

- `met`: Repo içinde uygulanmış ve test/CI kanıtı olan kontrol.
- `partial`: Temel iskelet veya kısmi kontrol var, staging/operasyon kanıtı veya ek uygulama gerekiyor.
- `planned`: Bu sürümde henüz uygulanmamış kontrol.

## Kontrol Özeti

| Alan | Durum | Kanıt | Sonraki aksiyon |
| --- | --- | --- | --- |
| Architecture and threat modeling | partial | `docs/04_SECURITY.md`, `docs/10_DECISIONS_AND_CHANGELOG.md` | Launch öncesi asset/trust boundary/abuse case threat model oluştur. |
| Authentication | met | `apps/security/forms.py`, `apps/security/totp.py`, `apps/security/admin_auth.py` | Staging'de gerçek staff TOTP cihazlarını provision et. |
| Session management | partial | `config/settings/production.py`, `apps/security/forms.py` | Kritik admin işlemleri için session timeout ve re-auth gözden geçir. |
| Access control | partial | `config/urls.py`, `apps/*/admin.py` | Django admin rol gruplarını tanımla ve test et. |
| Validation, sanitization, encoding | met | `apps/blog/models.py`, `apps/contact/forms.py`, `apps/core/structured_data.py` | XSS/escaping/form validation testlerini CI'da tut. |
| Cryptography and secrets | partial | `.env.example`, `ops/backup/create-encrypted-backup.sh`, `config/settings/production.py` | Production secret rotation ve saklama sahipliğini repo dışı dokümante et. |
| Error handling and logging | met | `apps/core/views.py`, `apps/core/logging.py`, `docs/MONITORING_LOGGING.md` | Production loglarını seçilen izleme backend'ine bağla. |
| Data protection and privacy | partial | `docs/CONTACT_EMAIL_REQUIREMENTS.md`, `apps/newsletter/models.py`, `apps/contact/models.py` | Gizlilik ve cookie public sayfalarını tamamla. |
| Communications security | met | `config/settings/production.py`, `docs/CLOUDFLARE_ORIGIN_LOCKDOWN.md`, `docs/SECURITY_HEADERS.md` | Staging/production domainlerinde strict TLS ve HSTS doğrula. |
| Security configuration | met | `apps/security/headers.py`, `nginx/default.cloudflare.conf`, `ops/cloudflare/waf-rate-limit-rules.json` | Sensitive file exposure ve Cloudflare rule smoke testlerini staging'de çalıştır. |
| Files and resources | partial | `docs/04_SECURITY.md`, `nginx/default.conf`, `nginx/default.cloudflare.conf` | Upload açıldığında image validation/re-encode kontrollerini uygula. |
| SSRF and outbound requests | met | `automation/http/client.py`, `automation/http/test_client.py` | Her yeni adapter için allowlist ve redirect/IP testlerini zorunlu tut. |
| Dependency and supply chain | partial | `pyproject.toml`, `.github/workflows/ci.yml` | Container image scan ve dependency update workflow ekle. |
| Backup and recovery | partial | `ops/backup/create-encrypted-backup.sh`, `ops/backup/restore-test.sh`, `docs/BACKUP_RESTORE.md` | İlk staging restore testini çalıştır ve RTO/RPO kanıtını kaydet. |

## Launch Gate

Launch öncesi `partial` kalan kontrollerden en az şu kanıtlar tamamlanmalıdır:

- Threat model dokümanı.
- Admin role/group testleri.
- Gizlilik ve cookie policy sayfaları.
- Staging restore testi.
- Staging sensitive file exposure smoke testi.
- Container image scan sonucu.

Bu liste “tam güvenli” iddiası değildir. Güvenlik; test, yama, izleme ve olay müdahalesi gerektiren sürekli bir süreçtir.
