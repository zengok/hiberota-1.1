# HibeRota Master Proje Planı

## 1. Amaç ve başarı tanımı

HibeRota'nın yeni sürümü, mevcut demo ürünün fikir ve kullanıcı akışını koruyarak sıfırdan kurulacak üretim sınıfı bir platformdur.

Başarılı ürün:

- yeni çağrıları resmi kaynaklardan saatlik veya kaynağa uygun periyotla keşfeder,
- veriyi kurallı şekilde normalize eder,
- duplicate kayıt üretmez,
- belirsiz veriyi otomatik yayımlamak yerine incelemeye gönderir,
- son başvuru tarihi geçen çağrıları doğru biçimde kapatır,
- öğrenciler, akademisyenler, araştırmacılar, girişimciler, KOBİ'ler, firmalar ve kurumlar için hızlı arama/filtreleme sunar,
- kaynak URL'sini, tarih bilgisini ve veri güncelliğini açıkça gösterir,
- mobil, erişilebilir, hızlı ve SEO uyumlu çalışır,
- admin dışındaki ziyaretçiler için hesap gerektirmez,
- 4 vCPU, 4 GB RAM, 60 GB disk ve 2 TB trafik kapasiteli AlmaLinux 9 VDS üzerinde kontrollü kaynak tüketir,
- ticari büyüme için dokümante, testli ve taşınabilir olur.

## 2. Kapsam

### Public ürün

- Ana sayfa
- Çağrılar
- Çağrı detay
- Kurumlar
- Kurum detay
- Blog / Proje Rehberi
- Blog detay
- Hibe anketi
- İletişim
- Favoriler
- E-bülten
- Yasal ve güvenlik sayfaları
- RSS/Atom veya JSON Feed
- Sosyal paylaşım ve güvenli embed kartı

### Yönetim ürünü

- Çağrı ve kurum yönetimi
- Kaynak ve adaptör yönetimi
- Crawl run ve kaynak sağlık görünümü
- Manual review kuyruğu
- Duplicate birleştirme
- Blog/yazar/içerik editörü
- İletişim mesajları
- E-bülten aboneleri ve gönderim kayıtları
- Anket kural yönetimi
- Audit log
- Sistem ayarları
- Kullanıcıya açık olmayan staff kimlik doğrulaması

### Kapsam dışı — ilk sürüm

- Public üyelik
- Kullanıcı profili
- Ödeme
- Mobil uygulama
- Yapay zekâ ile veri çıkarma
- Kaynak güvenlik mekanizmalarını aşma
- CAPTCHA çözme
- Herkese açık yazma API'si
- Çok dilli içerik üretimi; altyapı hazır olabilir fakat gerçek çeviri olmadan `hreflang` kullanılmaz

## 3. Önerilen sistem mimarisi

```text
Ziyaretçi
   |
Cloudflare DNS/CDN/WAF/DDoS/Rate Limit
   |
Nginx
   |
Gunicorn + Django
   |---------------- PostgreSQL (tek kalıcı kaynak)
   |---------------- Redis (queue/cache/lock)
   |---------------- Celery worker
   |---------------- Celery beat
   |---------------- E-posta sağlayıcısı
   |
Resmi dış kaynaklar
   ^
Kaynak adaptörleri + kontrollü HTTP istemcisi
```

### Neden modüler monolit?

Bu ürünün domaini güçlü fakat ilk ölçeği sınırlıdır. 4 GB RAM VDS üzerinde mikroservisler:

- operasyon maliyetini,
- gözlemlenebilirlik yükünü,
- ağ hatası riskini,
- deployment karmaşıklığını,
- Codex bağlam ihtiyacını

gereksiz artırır.

Django modüler monolit; admin paneli, SSR sayfalar, ORM, güvenlik middleware'leri ve Python scraper ekosistemini tek uygulama sınırında birleştirir. Modüller açık tutulduğu için ihtiyaç oluşursa worker veya arama servisi daha sonra ayrılabilir.

## 4. Uygulama modülleri

Önerilen Django app yapısı:

```text
apps/
  core/             ortak modeller, healthcheck, ayarlar
  calls/            çağrı domaini ve public sayfalar
  institutions/     kurum ve ülke/bölge ilişkileri
  taxonomy/         hedef kitle, tema, sektör, anahtar kelime ağacı
  sources/          kaynak kataloğu ve adaptör metadata
  ingestion/        crawl run, item, evidence, review ve duplicate
  search/           arama ve filtreleme
  blog/             yazar ve içerik
  survey/           hibe anketi ve eşleştirme
  newsletter/       abonelik ve gönderimler
  contact/          iletişim mesajları
  analytics/        anonim ürün olayları ve rapor yardımcıları
  security/         audit, rate-limit yardımcıları, security.txt
automation/
  adapters/
  pipeline/
  http/
  parsers/
  tasks/
config/
templates/
static/
media/
docs/
data/
```

`analytics` uygulaması Google Analytics'in yerine geçmez; yalnızca gerekli anonim iç ürün olaylarını veya admin raporlarını taşır.

## 5. Fazlar ve çıkış kapıları

### Faz 0 — Keşif ve envanter

Amaç: proje klasöründeki varlıkları kontrollü biçimde tanımak.

İşler:

- logo ve tasarım dosyalarının isim, tür, boyut ve kullanım amacını listele,
- Excel kaynak kataloğunun şemasını doğrula,
- mevcut demo siteden korunacak içerik/akışları listele,
- eksik secret ve kimlikleri belirle,
- domain, DNS, e-posta ve staging kararlarını yaz,
- ADR-001 teknoloji seçimini kaydet.

Çıkış kapısı:

- `ASSET_INVENTORY.md`,
- geçerli kaynak kataloğu,
- açık eksik bilgi listesi,
- onaylanmış mimari.

### Faz 1 — Repository ve geliştirme altyapısı

Amaç: test edilebilir, tekrarlanabilir iskelet.

İşler:

- Django proje yapısı,
- Docker Compose,
- local PostgreSQL/Redis,
- ortam bazlı ayarlar,
- healthcheck,
- CI,
- lint/type/test/security araçları,
- temel Nginx,
- örnek `.env`.

Çıkış kapısı:

- tek komutla local ayağa kalkma,
- CI yeşil,
- production ayar kontrolü,
- secret bulunmayan temiz repo.

### Faz 2 — Domain modeli ve admin

Amaç: çağrıların doğru ve izlenebilir biçimde saklanması.

İşler:

- veri modeli,
- state machine,
- taxonomy,
- FTS/trigram,
- admin CRUD,
- audit log,
- seed/import komutları.

Çıkış kapısı:

- örnek çağrı verisi admin ve public query katmanında doğru çalışır,
- constraint ve indeks testleri geçer,
- duplicate temel kuralları çalışır.

### Faz 3 — Otomasyon çekirdeği

Amaç: kaynak bağımsız ingestion hattı.

İşler:

- adapter sözleşmesi,
- kaynak kataloğu importu,
- güvenli HTTP client,
- scheduler,
- queue,
- normalize/validate/dedup/confidence/publish,
- review queue,
- kaynak sağlık ölçümleri,
- örnek adaptörler.

Çıkış kapısı:

- API/feed/static HTML tiplerinden en az birer adaptör,
- idempotent tekrar çalışma,
- aynı çağrının tekrar oluşmaması,
- 403/429 durumunda güvenli durma,
- fixture testleri.

### Faz 4 — Public ürün çekirdeği

Amaç: ana kullanıcı değerini sunmak.

İşler:

- ortak tasarım sistemi,
- ana sayfa,
- çağrı listesi,
- filtreler,
- detay,
- kurum listesi/detay,
- favoriler,
- mobil kullanım,
- erişilebilirlik.

Çıkış kapısı:

- public hesap olmadan tam gezinme,
- hızlı arama,
- mobil filtre,
- geçerli linkler,
- Lighthouse başlangıç hedefleri.

### Faz 5 — İçerik, anket, iletişim, e-bülten

Amaç: SEO içerik ve geri dönüş akışları.

Çıkış kapısı:

- blog admin editörü,
- anket sonucu açıklanabilir,
- mesajlar admin'e düşer,
- double opt-in ve unsubscribe çalışır,
- haftalık/aylık segment gönderimi test edilir.

### Faz 6 — SEO, analitik, reklam ve paylaşım

Amaç: keşfedilebilirlik ve ölçüm.

Çıkış kapısı:

- sitemap index,
- canonical/noindex kuralları,
- structured data validasyonu,
- GA4 consent-aware,
- AdSense yalnızca kimlik ve CMP hazırsa,
- RSS/feed,
- paylaşım/embed,
- Core Web Vitals bütçeleri.

### Faz 7 — Hardening ve operasyon

Amaç: üretim güvenliği ve sürdürülebilir işletim.

Çıkış kapısı:

- OWASP ASVS L1 kontrolü,
- Cloudflare/Nginx/firewall,
- admin 2FA,
- backup/restore testi,
- dependency/container taraması,
- log/monitoring/alert,
- güvenlik politikası.

### Faz 8 — Staging, geçiş ve lansman

Amaç: kontrollü üretim açılışı.

Çıkış kapısı:

- staging kabul testi,
- kontrollü kaynak importu,
- yük testi,
- DNS/SSL doğrulama,
- rollback provası,
- production smoke test,
- ilk 72 saat izleme planı.

## 6. Ürün KPI'ları

### Veri kalitesi

- Başarılı kaynak çalışma oranı
- Kaynak başına parse başarı oranı
- Duplicate oluşum oranı
- Manual review oranı
- Zorunlu alan doluluk oranı
- Deadline doğruluk örneklemi
- Bozuk resmi link oranı
- İlk görülme ile yayın arasındaki süre

### Kullanıcı deneyimi

- Arama sonucu tıklama oranı
- Filtre kullanımı
- Resmi başvuru bağlantısı tıklaması
- Favoriye ekleme
- Anket tamamlama
- Blogdan çağrıya geçiş
- E-bülten kayıt ve unsubscribe oranı
- Mobil bounce ve Core Web Vitals

### Operasyon

- Worker queue gecikmesi
- Crawl run süresi
- 403/429 oranı
- PostgreSQL disk büyümesi
- Backup başarısı
- Hata alarmına dönüş süresi
- Deployment rollback süresi

## 7. Kaynak kapasite bütçesi

Başlangıç production hedefi:

- Gunicorn: 2 worker, kontrollü thread sayısı
- Celery: concurrency 1–2
- Playwright: sürekli açık değil; ayrı kuyrukta concurrency 1
- Redis: bellek limiti ve eviction politikası
- PostgreSQL: ölçülmüş shared buffers/work memory
- 2 GB swap: yalnızca acil basınç tamponu, normal RAM yerine kullanılmaz
- Log rotation ve snapshot retention
- Static/media Cloudflare cache
- Liste ve ana sayfa sorgularında Redis/page fragment cache

Kaynak değerleri yük testine göre ayarlanmalıdır; tahminler doğrudan production gerçeği kabul edilmez.

## 8. Kritik ürün kararları

1. Favoriler `localStorage` kullanır; cihazlar arası senkronizasyon yoktur.
2. Anket cevabı hesap oluşturmaz; tercih sonucu yerel saklanabilir.
3. E-posta aboneliği profil değildir; sadece izin, sıklık ve teslim kayıtları tutulur.
4. Resmi başvuru bağlantısı her çağrı detayında birincil dış aksiyondur.
5. Kaynak bilgisi eksikse sistem tahmin üretmez; "resmi kaynakta belirtilmemiş" gösterir.
6. Otomatik yayın için alan bazlı minimum kalite eşiği gerekir.
7. Deadline geçmişse durum hesaplanır; kaynak tekrar açılış bildirmişse yeni sürüm veya tarih kaydı oluşturulur.
8. Kaynak engeli ile karşılaşınca sistem atlatma yapmaz; bekler, yavaşlar veya manuel/API gerekli durumuna geçer.
9. Demo kodu yeni mimarinin temeli kabul edilmez; yalnızca UX ve ürün referansıdır.
10. Teknik belge ve çalıştırma komutları her fazda güncel tutulur.

## 9. Lansman öncesi bloke edici eksikler

- AdSense client/publisher kimliği verilmeden reklam scripti üretimde açılmaz.
- Gerçek e-posta domaini ve SPF/DKIM/DMARC doğrulanmadan toplu gönderim yapılmaz.
- Cloudflare origin sertifikası ve firewall kuralı olmadan production açılmaz.
- Backup restore testi yapılmadan canlı veri import edilmez.
- Kaynak Excel'i doğrulanmadan toplu scheduler açılmaz.
- KVKK/GDPR/çerez metinleri hukuk incelemesi görmeden "hukuken tam uyumlu" olarak etiketlenmez.
