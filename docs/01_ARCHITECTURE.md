# Sistem Mimarisi

## 1. Mimari ilkeler

- Modüler monolit
- Server-side rendering
- Tek kalıcı veritabanı
- Idempotent arka plan işleri
- Kaynak bazlı adaptör
- Kanıtlanabilir veri kaynağı
- Varsayılan güvenli yapı
- Ölçmeden ölçeklendirmeme
- Public hesap olmadan kişiselleştirme
- İleride ayrıştırılabilir sınırlar

## 2. Runtime bileşenleri

### Web

Django template tabanlı SSR kullanılır. Bu yaklaşım:

- arama motoru taramasını kolaylaştırır,
- JavaScript bağımlılığını azaltır,
- 4 GB sunucuda düşük kaynak tüketir,
- Bootstrap ile mobil geliştirmeyi basitleştirir.

Filtre güncellemeleri için gerektiğinde küçük `fetch` istekleri veya HTMX değerlendirilebilir. HTMX zorunlu bağımlılık değildir; eklenirse ADR gerekir.

### PostgreSQL

Aşağıdaki verilerin tamamı PostgreSQL'de tutulur:

- çağrılar,
- kurumlar,
- taxonomy,
- kaynaklar,
- crawl run ve item kayıtları,
- review queue,
- duplicate kararları,
- blog,
- iletişim,
- abonelik,
- gönderim,
- audit log,
- sistem ayarları.

Üretimde SQLite kullanılmaz. SQLite yalnızca lokal prototip veya tek seferlik dönüşüm aracı olabilir.

### Redis

Redis yalnızca:

- Celery broker,
- kısa süreli cache,
- distributed lock,
- rate-limit sayaçları

için kullanılır.

İşin tamamlandığını kanıtlayan tek kayıt Redis değildir.

### Celery

Ayrı kuyruklar:

- `crawl_discovery`
- `crawl_detail`
- `link_check`
- `publication`
- `newsletter`
- `maintenance`
- `headless`

Queue timeout ve concurrency değerleri ayrı tanımlanır.

### Nginx

Nginx:

- TLS sonlandırma veya Cloudflare origin TLS,
- reverse proxy,
- static/media servis,
- request boyutu,
- timeout,
- rate limit savunma katmanı,
- güvenlik headerları

için kullanılır.

Nginx proje kökünü veya repo klasörünü hiçbir koşulda web root yapmaz.

## 3. Önerilen klasör yapısı

```text
hiberota/
  AGENTS.md
  README.md
  TASKS.md
  pyproject.toml
  uv.lock veya requirements lock
  compose.yaml
  compose.production.yaml
  Dockerfile
  .env.example
  .github/
    workflows/
  config/
    settings/
      base.py
      local.py
      test.py
      staging.py
      production.py
    urls.py
    celery.py
  apps/
  automation/
  templates/
  static/
  media/
  deploy/
    nginx/
    system/
    scripts/
  docs/
  data/
    source_catalog.xlsx
    imports/
  tests/
```

Gerçek source catalog dosyasının adı farklı olabilir. Kod dosya adını hard-code etmek yerine ayar veya yönetim komutu parametresi kullanır.

## 4. Request akışı

### Public çağrı listeleme

1. Cloudflare isteği filtreler.
2. Nginx kabul edilen host ve path'i Django'ya iletir.
3. Django filtre parametrelerini allowlist üzerinden doğrular.
4. Query service PostgreSQL indekslerini kullanır.
5. Sonuç sayfalı döner.
6. Template canonical/noindex kararını üretir.
7. Cache uygun ise response kısa süreli saklanır.

### Çağrı yayınlama

1. Adapter keşif URL'lerini bulur.
2. Item dedup kuyruğuna girer.
3. Detay kontrollü istemciyle alınır.
4. Parser ham alanları çıkarır.
5. Normalizer tarih/para/ülke/taxonomy dönüşümü yapar.
6. Validator zorunlu alanları kontrol eder.
7. Duplicate engine eşleşme arar.
8. Confidence engine yayın/review kararını verir.
9. PostgreSQL transaction içinde kayıt ve evidence yazılır.
10. Cache ve sitemap güncelleme sinyali üretilir.

## 5. Cache politikası

- Ana sayfa son çağrılar: 2–5 dakika
- Kurum çağrı sayıları: 5–15 dakika
- Çağrı detay: yayın kaydı değişene kadar veya kısa TTL
- Blog detay: publish/update ile invalidation
- Filtered list: yalnızca sık kullanılan ve güvenli kombinasyonlar
- Admin ve kişisel localStorage verisi cache edilmez
- Contact/newsletter POST yanıtları CDN cache edilmez

Cache key içinde dil, sayfa, filtre, sıralama ve gerekli varyasyon bulunur. Kullanıcı girdisi sınırsız cache key üretmemelidir.

## 6. İleride ölçekleme

Aşağıdaki sinyaller oluşmadan servis ayrıştırılmaz:

- PostgreSQL araması ölçülmüş şekilde yetersiz kalırsa Meilisearch/OpenSearch,
- worker web performansını etkilerse ayrı worker sunucusu,
- medya büyürse S3 uyumlu object storage,
- e-posta hacmi artarsa ayrı notification service,
- public veri tüketimi artarsa versioned read-only API.

Her ayrıştırma ADR ve ölçümle gerekçelendirilir.
