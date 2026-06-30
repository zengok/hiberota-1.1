# Güvenlik Mimarisi ve Politikası

## 1. Tehdit modeli

Korunacak varlıklar:

- kaynak kodu ve proje dosyaları,
- environment secretları,
- PostgreSQL verisi,
- admin hesapları,
- e-posta aboneleri,
- iletişim mesajları,
- crawl konfigürasyonu,
- yedekler,
- deployment erişimi.

Temel tehditler:

- bot/DDoS ve kaynak tüketimi,
- SQL injection,
- XSS,
- CSRF,
- SSRF,
- path traversal,
- gizli dosya ifşası,
- admin brute force,
- kötü amaçlı dosya yükleme,
- dependency/supply-chain açığı,
- scraper üzerinden iç ağa erişim,
- loglarda kişisel veri/secrets,
- yanlış Nginx alias/root yapılandırması,
- yedek dosyasının public alanda kalması.

## 2. Ağ katmanı

### Cloudflare

- DNS proxy aktif.
- TLS Full (Strict).
- Managed WAF kuralları.
- Bot ve DDoS koruması.
- `/admin`, `/contact`, `/newsletter`, `/survey`, `/api` için davranışa uygun rate limit.
- Static cache.
- Gerekiyorsa Turnstile.
- Gerçek ziyaretçi IP başlıkları yalnızca güvenilen Cloudflare proxylerinden kabul edilir.

### Origin kilitleme

- 80/443 sadece Cloudflare IP aralıklarından kabul edilir.
- SSH yalnızca sabit yönetici IP, VPN veya güvenli bastion üzerinden.
- PostgreSQL 5432 ve Redis 6379 public değildir.
- Gereksiz servis ve portlar kapalıdır.
- ICMP/ping'in tamamen kapatılması güvenlik için yeterli veya zorunlu değildir; asıl koruma port, servis, dosya yolu ve yetkilendirme katmanlarındadır.
- Ping veya port taraması proje dosyasına erişim sağlamamalıdır.

## 3. AlmaLinux 9 hardening

- Güncel güvenlik yamaları.
- Ayrı sudo yetkili deployment kullanıcısı.
- SSH key-only.
- Root login kapalı.
- PasswordAuthentication kapalı.
- firewalld.
- fail2ban.
- SELinux enforcing; gereksiz kapatma yok.
- Audit/log rotation.
- Docker daemon socket public veya uygulamaya mount edilmez.
- Containerlar mümkünse non-root.
- Read-only filesystem uygulanabilen servislere uygulanır.
- Resource limit.
- Host üzerinde `.env` izinleri minimum.

## 4. Nginx dosya izolasyonu

Kurallar:

- Proje root web root değildir.
- Sadece `/static/` ve kontrollü `/media/` alias edilir.
- `autoindex off`.
- Dotfile istekleri engellenir; yalnızca `.well-known` gerekli dosyaları allowlist.
- `.env`, `.git`, `.svn`, backup, SQL, SQLite, YAML config, log, source map ve editor temp dosyaları engellenir.
- Yanlış path fallback ile başka dosya döndürülmez.
- Symlink davranışı kontrol edilir.
- Media klasöründe script çalıştırılmaz.
- Upload response'ları doğru Content-Type ve `X-Content-Type-Options: nosniff` taşır.
- Hassas dosyalar ayrı private storage içindedir.

## 5. Uygulama güvenliği

- Django production checklist.
- `DEBUG=False`.
- Secret key environment secret.
- Strict `ALLOWED_HOSTS`.
- Secure cookies.
- CSRF trusted origins minimum.
- Session cookie admin için secure/httponly/samesite.
- HSTS preload kararı subdomain doğrulamasından sonra.
- HTTPS redirect.
- CSP nonce/hash.
- `frame-ancestors` varsayılan deny; embed endpointleri ayrı politika.
- Referrer-Policy.
- Permissions-Policy.
- X-Content-Type-Options.
- Clickjacking koruması.
- Güvenli host header.
- Parametreli ORM.
- Server-side validation.
- HTML sanitizasyonu yalnızca blog rich-text alanında allowlist tabanlı.
- Admin audit log.

## 6. Admin güvenliği

- Public kullanıcı kaydı yoktur.
- Admin hesabı yalnızca staff tarafından oluşturulur.
- TOTP 2FA.
- Güçlü parola ve breach kontrolü.
- Login rate limit.
- Oturum süresi ve tekrar doğrulama.
- İsteğe bağlı IP/VPN kısıtı.
- Varsayılan `/admin/` adresi değiştirilebilir fakat bu tek güvenlik önlemi sayılmaz.
- Yetki grupları:
  - Super Admin
  - Content Editor
  - Data Reviewer
  - Automation Operator
  - Support/Contact
- En az yetki ilkesi.
- Kritik işlemler audit edilir.

## 7. Form ve spam güvenliği

Contact, newsletter ve survey:

- CSRF
- hidden honeypot
- zaman tabanlı bot sinyali
- IP ve hedef bazlı rate limit
- mesaj/email uzunluk sınırı
- e-posta normalization
- disposable mail politikası gerekiyorsa dikkatli kullanım
- Turnstile yalnızca ihtiyaç halinde
- hata mesajında hesap/e-posta varlığı sızdırmama
- tekrar gönderim idempotency

## 8. Dosya yükleme

Blog görselleri:

- JPEG/PNG/WebP allowlist
- uzantı + MIME + magic byte kontrolü
- boyut ve piksel limiti
- metadata temizleme
- Pillow ile yeniden decode/encode
- rastgele dosya adı
- kullanıcı sağladığı path kullanılmaz
- SVG varsayılan yasak
- private temp klasörü
- image bomb koruması
- gerekirse ClamAV
- alt text zorunlu
- telif/kaynak alanı

## 9. Scraper SSRF güvenliği

- Kaynak domain allowlist.
- URL scheme yalnızca HTTPS; zorunlu kaynak için açık onaylı HTTP.
- Userinfo içeren URL reddi.
- DNS çözümünden sonra IP sınıfı kontrolü.
- Redirect sonrası tekrar kontrol.
- `localhost`, RFC1918, link-local, metadata IP'leri, Unix socket erişimi engeli.
- Port allowlist 80/443.
- Response size limit.
- XML external entity kapalı.
- Archive/decompression limitleri.
- Kaynak tarafından döndürülen URL otomatik sistem komutu veya local file path olarak kullanılamaz.

## 10. Secret ve supply chain

- Secret repo içinde yok.
- `.env.example` yalnızca placeholder.
- Production secret rotate edilebilir.
- GitHub secret scanning.
- Dependabot/Renovate.
- `pip-audit`, Bandit, container scan.
- Lock file.
- Paket ekleme ADR veya gerekçe.
- Yüksek/kritik CVE deployment'ı bloke eder.
- Build sırasında rastgele remote script pipe-to-shell kullanılmaz.

## 11. Backup

- Günlük PostgreSQL logical backup.
- Düzenli volume/snapshot.
- Uzak ve şifreli kopya.
- Retention politikası.
- Backup adı ve konumu public web root dışında.
- Aylık restore testi.
- Restore RTO/RPO kaydı.
- Backup erişimi audit.

## 12. Public güvenlik politikası

Public `/guvenlik/` sayfası:

- güvenliğe verilen önem,
- kapsam,
- sorumlu bildirim yöntemi,
- bildirime eklenecek bilgiler,
- iyi niyetli araştırma kuralları,
- yasak testler: DDoS, veri silme, sosyal mühendislik, kalıcılık,
- yanıt süreci,
- gizlilik,
- yasal çerçeve uyarısı

içerir.

Ayrıca `.well-known/security.txt` oluşturulur.

Public sayfa; firewall, IP, admin path, kullanılan secret yönetimi veya saldırgana yararlı ayrıntıları açıklamaz.

## 13. Doğrulama standardı

İlk ticari sürüm için OWASP ASVS Level 1 taban çizgisi hedeflenir. Kritik admin, upload ve scraper URL fetch alanlarında seçilmiş Level 2 kontrolleri uygulanır.

"Tam güvenli" ifadesi kullanılmaz. Güvenlik; test, yama, izleme ve olay müdahalesi gerektiren sürekli süreçtir.
