# HibeRota — Codex Çalışma Talimatları

## 1. Projenin amacı

HibeRota; dünyadaki kamu kurumları, belediyeler, kalkınma ajansları, üniversiteler, ülke birlikleri ve fon sağlayıcıların yayımladığı hibe, fon ve proje çağrılarını belirlenmiş kaynaklardan düzenli olarak toplayan, normalize eden, doğrulayan ve kullanıcıya SEO uyumlu çok sayfalı bir web sitesi üzerinden sunan platformdur.

Bu projede halka açık kullanıcı hesabı veya profil sistemi YOKTUR. Yalnızca yetkili personel için güvenli yönetim paneli bulunur.

MVP aşamasında yapay zekâ API'si KULLANILMAZ. İleride eklenebilmesi için bağımsız bir genişleme arayüzü bırakılır; AI entegrasyonu mevcut veri toplama ve yayınlama akışının zorunlu parçası yapılamaz.

## 2. Değiştirilemez mimari kararlar

Codex aşağıdaki kararları açık bir ADR ve insan onayı olmadan değiştiremez:

- Backend ve sunucu taraflı web: Django 5.2 LTS.
- Dil: Python 3.12 taban çizgisi.
- Veritabanı ve kalıcı sistem durumu: PostgreSQL.
- Kuyruk ve kısa süreli cache: Redis.
- Arka plan işleri: Celery worker + Celery beat.
- Web sunucusu: Nginx + Gunicorn.
- Arayüz: Django templates + Bootstrap 5.3 + sınırlı Vanilla JavaScript.
- Filtreleme ve arama: PostgreSQL full-text search + `pg_trgm`.
- Üretim dağıtımı: Docker Compose.
- CDN/WAF/DDoS katmanı: Cloudflare.
- Public kullanıcı üyeliği: yok.
- Public favoriler ve anket tercihleri: tarayıcı `localStorage` içinde; hassas veri tutulmaz.
- Yönetici kimlik doğrulaması: Django staff hesabı, güçlü parola, TOTP 2FA ve rate limit.
- Tek kalıcı kaynak PostgreSQL'dir. Üretimde otomasyon state'i SQLite içinde tutulmaz.
- Redis içeriği kalıcı iş kaydı veya sistem doğruluğu için kaynak kabul edilmez.
- Tüm çağrı bilgilerinde resmi kaynak URL'si ve veri kaynağı izlenebilirliği zorunludur.
- Anti-bot mekanizması, CAPTCHA, erişim kontrolü veya kaynak güvenliği atlatılamaz.

## 3. Codex bağlam ve token politikası

Her görevde:

1. Önce yalnızca bu `AGENTS.md` dosyasını oku.
2. Ardından `docs/09_CODEX_CONTEXT_MAP.md` içinden görevle ilgili en fazla iki belgeyi seç.
3. İlgisiz klasörleri, tüm binary varlıkları, logo dosyalarını ve Excel kaynak kataloğunu topluca okuma.
4. Excel dosyasına ihtiyaç varsa önce yalnızca sayfa adlarını, sütun başlıklarını ve ilk 5 örnek satırı incele.
5. Tek görevde bir dikey iş dilimi uygula. Büyük bir fazı tek görevde tamamlamaya çalışma.
6. Aynı bilgiyi farklı dokümanlarda tekrar üretme; mevcut dokümana bağlantı ver.
7. Gereksiz yorum, soyutlama, paket veya yardımcı sınıf oluşturma.
8. Mevcut çözüm yeterliyse yeni framework veya servis ekleme.
9. Değişiklik 15'ten fazla dosyaya yayılacaksa önce kısa uygulama notu oluştur ve işi alt görevlere böl.
10. Her görev sonunda yalnızca:
   - kısa özet,
   - değişen dosyalar,
   - çalıştırılan testler,
   - kalan risk,
   - önerilen sonraki görev
   raporlanır.

## 4. Görev uygulama sırası

Her geliştirme görevinde aşağıdaki sıra zorunludur:

1. İlgili kabul kriterini belirle.
2. Etkilenecek dosyaları listele.
3. Önce test veya doğrulama yaklaşımını belirle.
4. En küçük güvenli değişikliği uygula.
5. Hedef testleri çalıştır.
6. Lint/type/security kontrollerini çalıştır.
7. İlgili dokümantasyonu güncelle.
8. `git diff` ve `git status` kontrolü yap.
9. Gizli bilgi, anahtar, token veya kişisel veri eklenmediğini doğrula.

## 5. Kod kalitesi kuralları

- Python kodu type hint içermelidir.
- İş kuralları view veya template içine gömülmemelidir.
- Servis ve domain katmanı yalnızca gerçek tekrar veya karmaşık iş kuralı varsa kullanılmalıdır.
- Fonksiyonlar tek sorumluluk taşımalıdır.
- Tarih/saat verileri UTC saklanmalı, kullanıcıya uygun yerel saatle gösterilmelidir.
- Para değerleri `Decimal` ve ISO 4217 para birimi koduyla tutulmalıdır.
- Ülke kodları ISO 3166-1 alpha-2 olmalıdır.
- Kaynak URL'leri normalize edilmeli fakat resmi URL ayrıca korunmalıdır.
- Kullanıcı girdisi her zaman sunucu tarafında doğrulanmalıdır.
- Raw SQL yalnızca ölçülmüş performans gerekçesiyle ve parametreli sorgu olarak kullanılabilir.
- Template çıktıları varsayılan escape davranışını korumalıdır.
- `mark_safe`, doğrudan HTML enjeksiyonu ve dinamik `eval` kullanılmaz.
- Migration dosyaları elle silinmez veya yeniden yazılmaz.
- Üretim verisi geliştirme ortamına kopyalanmaz.

## 6. Güvenlik sınırları

- Proje kökü, `.git`, `.env`, backup, log, migration dump veya kaynak kod Nginx üzerinden servis edilmez.
- Nginx yalnızca açıkça tanımlanmış static/media yollarını servis eder.
- Directory listing kapalıdır.
- PostgreSQL ve Redis internete açık port dinlemez.
- Admin paneli public kullanıcı işlevi değildir.
- İletişim, anket ve e-bülten uçları rate limit, CSRF, spam koruması ve doğrulama içerir.
- Dosya yüklemeleri MIME, uzantı, boyut ve görüntü yeniden kodlama kontrollerinden geçer.
- SVG yüklemesi varsayılan olarak yasaktır.
- Dış URL erişimi SSRF korumalı allowlist, DNS/IP kontrolü, redirect sınırı ve response boyutu sınırı kullanır.
- Kaynak adaptörleri CAPTCHA çözmez, login duvarını aşmaz, proxy rotasyonu veya fingerprint gizleme kullanmaz.
- Güvenlik kontrolünü zayıflatan "geçici" çözüm uygulanmaz.

## 7. Scraper/adaptör kuralları

Kaynak erişim sırası:

1. Resmi API
2. Resmi RSS/Atom/JSON feed
3. Resmi sitemap
4. Statik liste/detay HTML
5. İzinli ve zorunluysa sınırlı headless browser

Her kaynak adaptörü:

- açık bir kaynak kimliği taşır,
- robots.txt ve kullanım koşulu durumunu kaydeder,
- tanımlı user-agent ve iletişim adresi kullanır,
- host bazında concurrency ve istek aralığı uygular,
- timeout, retry, exponential backoff, jitter ve circuit breaker uygular,
- `Retry-After`, `ETag` ve `Last-Modified` başlıklarını destekler,
- 401/403/429 durumlarında agresif tekrar yapmaz,
- erişim engelini aşmaya çalışmaz,
- parse başarısını fixture testleriyle doğrular,
- ham sayfa yerine yalnızca gerekli kanıt metnini ve hash'i saklar,
- başarısızlıkta kaynak sağlığı ve inceleme kaydı üretir.

## 8. Test zorunluluğu

Değişikliğe göre aşağıdaki kontrollerden ilgili olanları çalıştır:

```bash
python manage.py check
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run
pytest
ruff check .
ruff format --check .
mypy .
bandit -r apps config automation
pip-audit
```

Frontend değişikliklerinde:

- 320 px, 375 px, 768 px, 1024 px ve 1440 px görünüm doğrulaması,
- klavye kullanımı,
- focus görünürlüğü,
- form hata mesajları,
- Lighthouse veya eşdeğer performans kontrolü yapılır.

## 9. Git ve iş akışı

- `main` doğrudan geliştirme dalı olarak kullanılmaz.
- Dal isimleri: `feat/...`, `fix/...`, `security/...`, `docs/...`, `chore/...`.
- Bir worktree tek bir issue veya dikey iş dilimi içindir.
- Aynı dosyalar farklı worktree'lerde eş zamanlı değiştirilmez.
- Küçük ve geri alınabilir commitler oluşturulur.
- PR açıklaması kapsam, test, migration, güvenlik etkisi ve rollback notu içerir.
- Generated, vendor, media, cache, `.env` ve veritabanı dump dosyaları commitlenmez.

## 10. Tamamlanmış sayılma şartı

Bir görev aşağıdakiler olmadan tamamlanmış değildir:

- Kabul kriterleri karşılanmış.
- Testler geçmiş.
- Güvenlik ve veri kaynağı izlenebilirliği korunmuş.
- Mobil ve erişilebilirlik etkisi kontrol edilmiş.
- İlgili dokümantasyon güncellenmiş.
- Gizli bilgi repoya girmemiş.
- Geri alma yöntemi belirtilmiş.
