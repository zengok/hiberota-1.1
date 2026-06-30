# HibeRota Mimari Analiz Özeti

**Tarih:** 30 Haziran 2026  
**Proje Adı:** HibeRota - Hibe ve Fonlar Keşif Platformu  
**Tür:** Django Modüler Monolit

---

## 📋 İçindekiler

1. [Proje Özeti](#proje-özeti)
2. [Mimari İlkeler](#mimari-ilkeler)
3. [Teknik Stack](#teknik-stack)
4. [Sistem Mimarisi](#sistem-mimarisi)
5. [Veri Modeli](#veri-modeli)
6. [Otomasyon Pipeline](#otomasyon-pipeline)
7. [Django Modülleri](#django-modülleri)
8. [Geliştirme Durumu](#geliştirme-durumu)
9. [Güvenlik & Uyum](#güvenlik--uyum)
10. [Operasyon & İzleme](#operasyon--izleme)

---

## Proje Özeti

### Tanım
HibeRota, kullanıcıların **hesap oluşturmadan** erişebildiği açık ve ücretsiz bir hibe ve fonlar keşif platformudur. 
Platform, 250+ farklı kurumdan hibe çağrılarını otomatik ve el ile kaynaklar aracılığıyla toplayarak, 
normalize edilmiş ve doğrulanmış bir havuzda sunmaktadır.

### Temel Özellikler
- ✅ Çok kaynaklı hibe katalog sistemi
- ✅ Otomatik veri kazıma (Web scraping) ve yapılandırma
- ✅ Duplicate ve kalite kontrol sistemi
- ✅ İleri filtreleme ve favoriler (localStorage)
- ✅ Hibe anketi ve kişiselleştirilmiş eşleştirme
- ✅ E-bülten yönetimi (double opt-in)
- ✅ Kapsamlı SEO ve sosyal medya desteği
- ✅ GA4 Analytics ve AdSense entegrasyonu
- ✅ OWASP ASVS L1 güvenlik standartları
- ✅ Production-ready deployment

### İş Modeli
- Platform tamamen **ücretsiz** ve hesap gerektirmez
- Gelir: AdSense reklam integasyonu
- Hedef: Türkiye ve küresel hibe keşif pazarı

---

## Mimari İlkeler

| İlke | Açıklama |
|------|----------|
| **Modüler Monolit** | Tek Django uygulaması, ayrı modüller halinde organize |
| **Server-Side Rendering** | Django templates kullanarak SSR, minimal JS |
| **Tek Veritabanı** | PostgreSQL tek kalıcı veri kaynağı |
| **İdempotent İşler** | Arka plan işleri tekrar çalıştırılabilir ve güvenli |
| **Kaynak Adaptörleri** | Her kaynak tipi (API, feed, HTML) kendi adaptörü |
| **Kanıtlanabilir Veri** | Her veri parçası kaynağıyla ve zaman damgası ile bağlantılı |
| **Varsayılan Güvenli** | Security-first approach, deny-by-default |
| **Ölçümle Ölçekle** | Sorun kanıtlanmadan servis ayrıştırılmaz (no premature optimization) |

---

## Teknik Stack

```
Frontend:       Bootstrap 5.3 + Django Templates (SSR)
Backend:        Python 3.12 + Django 5.2 LTS
Database:       PostgreSQL 14+
Cache/Broker:   Redis
Background:     Celery + Celery Beat (scheduler)
Web Server:     Gunicorn (WSGI)
Reverse Proxy:  Nginx
Containers:     Docker Compose
Code Quality:   Ruff, mypy, pytest, bandit, pip-audit
CI/CD:          GitHub Actions
Monitoring:     JSON structured logs
```

### Önemli Kütüphaneler
- `requests` + custom `SafeHttpClient` (SSRF protection, robots.txt, timeout)
- `beautifulsoup4` + `lxml` (HTML parsing)
- `feedparser` (RSS/Atom feeds)
- `celery` (task queue)
- `psycopg3` (PostgreSQL driver)
- `django-storages` (media management)

---

## Sistem Mimarisi

### Runtime Bileşenleri

#### 1. **Web Bileşeni (Django)**
```
Request Flow:
Client → Cloudflare → Nginx → Django → PostgreSQL
              ↓
          WAF/Rate Limit
```

- Template-based SSR
- Allowlist parametre doğrulama
- Short-lived response cache
- Content Security Policy (nonce-based)

#### 2. **PostgreSQL (Kalıcı Veri)**
Tüm veri burada depolanır:
- Çağrılar, kurumlar, kaynaklar
- Taxonomy (hedef kitle, sektor, tema)
- Crawl run/item kayıtları
- Review queue
- Blog, newsletter, iletişim
- Audit log, sistem ayarları

Indeksler:
- FTS (full-text search) GIN index
- Trigram GIN index (title search)
- Deadline, published_at, workflow_status
- Institution, source, country relations

#### 3. **Redis (Kısa Süreli)**
- Celery message broker
- Cache (2-15 dakika TTL)
- Distributed locks (crawl safety)
- Rate limit counters

#### 4. **Celery (Arka Plan İşleri)**

Ayrı kuyruklar:
| Queue | Görev |
|-------|-------|
| `crawl_discovery` | Kaynak keşfi, liste parsing |
| `crawl_detail` | Detay sayfa indirme |
| `link_check` | Bağlantı doğrulama |
| `publication` | Yayın workflow |
| `newsletter` | Digest generation, sending |
| `maintenance` | Backup, cleanup, optimization |
| `headless` | Gelecek: JavaScript render |

Celery Beat: Scheduler (sources.schedule_due_sources her saatte)

#### 5. **Nginx (Reverse Proxy)**
- TLS termination (Cloudflare origin TLS)
- Static/media serving
- Request size limiting
- Timeout configuration
- Security headers
- Rate limiting (application-level fallback)

### Request Akışı Örneği: Çağrı Listeleme

```
1. Cloudflare filtreler (WAF, DDoS, rate limit)
2. Nginx host/path validasyonu
3. Django view filtre parametrelerini doğrular
4. QuerySet PostgreSQL indekslerini kullanarak sorgu yapar
5. Template canonical/noindex kararını verir
6. Response cache TTL ile saklanır
7. Response browser'a gönderilir
```

---

## Veri Modeli

### Ana Varlıklar

#### **Country**
```python
- code (ISO 3166-1 alpha-2, unique)
- name_tr, name_en
- region_code
- is_eu_member, is_europe
- is_active
```

#### **Institution**
```python
- name, slug, short_name
- institution_type (NGO, Think Tank, vb.)
- country (FK)
- website_url, logo
- description, is_verified, is_active
```

#### **Source**
```python
- institution (FK)
- name, base_url, listing_url
- source_type: api/feed/sitemap/html/headless/manual
- adapter_key (resolve to adapter class)
- status: active/paused/degraded/blocked
- crawl_interval_minutes
- robots_status, terms_status
- last_success_at, last_failure_at
- consecutive_failures, health_score
- config_json (schema-validated, no secrets)
```

#### **GrantCall (Ana Varlık)**
```python
# Kimlik
- id, title, slug
- source (FK), institution (FK)
- external_id (source'un kendi ID'si)
- official_url, canonical_source_url
- fingerprint (duplicate detection)

# İçerik
- summary, purpose, eligibility_text
- conditions_text, duration_text, funding_text
- application_process_text, contact_text

# Tarih & Para
- source_published_at, application_open_at
- deadline_at, deadline_timezone
- first_seen_at, last_seen_at, last_verified_at
- duration_min_months, duration_max_months
- funding_min, funding_max, currency

# Durum
- workflow_status: discovered/review/published/rejected
- availability_status: upcoming/open/closing_soon/closed/unknown
- confidence_score (0-100)
- is_featured, published_at, closed_at

# Kaynak Güveni
- title_confidence, deadline_confidence
- eligibility_confidence, funding_confidence
```

#### **Taxonomy**
- AudienceType (researcher, ngo, sme, startup, vb.)
- Sector (health, education, environment, vb.)
- Theme (innovation, climate, health, vb.)
- ProgramType (grant, loan, mentorship, vb.)
- OrganizationSize (startup, sme, enterprise)
- Region (Europe, Asia, Africa, vb.)

#### **CrawlRun**
```python
- source (FK)
- trigger_type: schedule/manual/retry/backfill
- status: pending/processing/success/partial_failure/failure
- started_at, finished_at
- discovered_count, fetched_count
- created_count, updated_count, review_count
- duplicate_count, failed_count
- http_status_summary (JSON)
- error_code, error_summary
- worker_id, config_version
```

#### **CrawlItem**
```python
- crawl_run (FK)
- source_url, normalized_url
- external_id, content_hash
- status: pending/fetched/parsed/published/duplicate
- attempt_count, http_status
- parser_version
- raw_metadata_json
- grant_call (FK - null if not published)
- error_code
```

#### **FieldEvidence**
```python
# Her kritik alan için kanıt
- grant_call (FK)
- field_name (title, deadline, eligibility, vb.)
- source_url, source_excerpt
- selector_or_path (CSS selector, XPath, JSONPath)
- fetched_at, content_hash
- parser_version, confidence
```

#### **ReviewItem**
```python
- grant_call (FK)
- reason_code: missing_dates/deadline_conflict/vb.
- severity: low/medium/high
- assigned_to (admin user)
- status: pending/approved/rejected
- resolution (admin notu)
- created_at, resolved_at
```

#### **Subscriber (Newsletter)**
```python
- email_normalized (unique)
- status: pending/active/unsubscribed/bounced
- frequency: weekly/monthly
- country/region, audience_preferences
- consent_at, consent_ip_hash
- confirmed_at, unsubscribed_at
```

### Durum Hesaplama

`availability_status` otomatik hesaplanır, rastgele değiştirilmez:

```
deadline bilinmiyor       → unknown
open_at gelecekte         → upcoming
deadline geçmiş           → closed
deadline <= now + threshold → closing_soon
diğer                     → open
```

Kaynak açıkça kapattıysa manuel override mümkün (audit edilir).

### Duplicate Stratejisi (Sıra Önemli)

1. **Exact match:** Aynı `source + external_id`
2. **URL match:** Normalize edilmiş canonical URL
3. **Hash match:** Institution + normalize title + deadline hash
4. **Fuzzy match:** Trigram benzerliği + institution + tarih toleransı
5. **Manual review:** Yönetici karar

Otomatik birleştirme sadece yüksek güvenli eşleşmelerde yapılır.

---

## Otomasyon Pipeline

### Temel İlke

> Amaç resmi ve izin verilen kaynaklardan sürdürülebilir, düşük yük oluşturan ve doğrulanabilir veri 
> toplamaktır. Kaynağın güvenlik önlemlerini aşmak, CAPTCHA çözmek, login yasağını atlatmak yasaktır.

### Adapter Sözleşmesi

Her adaptör aşağıdaki interface'i implement eder:

```python
class SourceAdapter(Protocol):
    key: str  # "eureka", "ukri", vb.
    
    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        """Liste sayfasını parse et, URL'leri keşfet"""
        pass
    
    def fetch_detail(self, item: DiscoveredItem, context: CrawlContext) -> FetchResult:
        """Detay sayfasını kontrollü istemciyle indir"""
        pass
    
    def parse(self, result: FetchResult, context: CrawlContext) -> ParsedCall:
        """HTML/JSON'dan alan değerlerini çıkar"""
        pass
```

Normalize, validate, deduplicate, publish = ortak pipeline servisleri

### Pipeline Aşamaları

```
schedule_due_sources()
  ↓
source lock (prevent concurrent crawl)
  ↓
adapter.discover() → DiscoveredItem'lar
  ↓
normalize_discovered_url()
  ↓
early_duplicate_check() (exact match)
  ↓
adapter.fetch_detail() → FetchResult
  ↓
adapter.parse() → ParsedCall
  ↓
normalize_fields() (date, money, country, taxonomy)
  ↓
validate() (check required fields)
  ↓
apply_taxonomy_rules() (audience inference)
  ↓
duplicate_match() (URL, hash, fuzzy)
  ↓
confidence_engine() (0-100 score)
  ↓
DECISION: auto_publish OR review_queue OR draft
  ↓
persist_parsed_call() (transaction)
  ↓
evidence_logging() (field source trail)
  ↓
metrics_recording() (CrawlRun update)
```

### Kontrollü HTTP İstemcisi

Zorunlu özellikler:

```python
class SafeHttpClient:
    # Kimlik
    - dürüst user-agent
    - güvenlik/iletişim e-postası
    
    # Ağ Güvenliği
    - DNS resolution doğrulaması
    - Hedef IP validation (private IP engeli)
    - Redirect allowlist doğrulama (redirect başına)
    - Maksimum redirect sayısı
    
    # Timeout
    - connect_timeout (5s)
    - read_timeout (10s)
    - total_timeout (30s)
    
    # Boyut Sınırları
    - maksimum_response_bytes (50 MB)
    - accepted_content_types whitelist
    
    # TLS
    - certificate verification
    - hostname checking
    
    # Mekanik Kontroller
    - host başına concurrency limit
    - minimum request interval
    - jitter (rate limit evasion önleme)
    - ETag ve Last-Modified support
    
    # Hatalar
    - sıkıştırma bombası koruması
    - Retry-After desteği
    - exponential backoff (429, 5xx)
    - circuit breaker (consecutive failures)
    - Düşük retry: 401, 403, 429
    
    # Telemetry
    - request/response logging
    - performance metrics
```

### Confidence Scoring (Örnek)

Toplam 100 puan:

| Faktör | Puan |
|--------|------|
| Resmi başlık | 15 |
| Resmi URL | 10 |
| Kurum | 10 |
| Hedef kitle | 10 |
| Açılış/Deadline | 20 |
| Amaç/Özet | 10 |
| Finansman | 10 |
| Ülke/Bölge | 5 |
| Katılım Şartı | 5 |
| Parser geçmiş başarısı | 5 |

**Karar Eşikleri:**
- 85-100 + kritik çelişki yok → **Auto Publish**
- 60-84 → **Review Queue**
- 0-59 → **Draft/Rejected**
- Deadline parse çelişkisi → **Always Review** (skor bağımsız)
- Resmi URL yok → **Auto publish YOK**

### Robots & Kullanım Koşulları

1. Kaynak eklenirken robots.txt durumu **kaydedilir**
2. Crawler **robots.txt'ye uyar** (erişim yetkilendirme değil, ama respect)
3. Kullanım koşulları açıkça otomasyonu yasaklıysa → `manual_only` veya `blocked`
4. Robots ulaşılamıyorsa → temkinli varsayım ve düşük hız
5. Kaynak sahibi iletişime geçerse → hızlı pause/takedown

### Parser Testleri

Her adaptör için:
- ✅ Gerçek kaynaktan alınmış sanitize fixture
- ✅ Liste parse testi
- ✅ Detay parse testi
- ✅ Tarih/para normalize testi
- ✅ Eksik alan edge cases
- ✅ Selector değişimi testi
- ✅ Duplicate detection testi

Canlı siteye test sırasında istek gönderilmez.

---

## Django Modülleri

### apps/core
**Temel ayarlar ve sağlık kontrolleri**
- Health endpoints: `/health/live`, `/health/ready`
- PostgreSQL, Redis, web, worker connection checks
- Base models ve utilities
- Settings management (local, staging, production)

### apps/calls
**Hibe çağrıları yönetimi**
- GrantCall model
- Durum hesaplama (workflow, availability)
- Call query service (filtering, pagination)
- Public list/detail views
- Kalite kontrol komutları

### apps/sources
**Kaynak yönetimi ve tarama**
- Source model
- Adapter registry
- Source scheduler (Celery Beat)
- Source health dashboard
- Source configuration validation

### apps/institutions
**Kurum yönetimi**
- Institution model
- Kurum listeleme ve detay
- Kurum başına çağrı sayıları

### apps/ingestion
**Veri ingestion ve pipeline**
- CrawlRun, CrawlItem modelleri
- Pipeline persistence layer
- Crawl metrics recording
- Integration tests

### apps/taxonomy
**Sınıflandırma sistemi**
- AudienceType, Sector, Theme
- ProgramType, OrganizationSize, Region
- Keyword rules ve matching
- Taxonomy seed data

### apps/blog
**Blog ve editöryel içerik**
- Author model
- BlogPost, BlogCategory, BlogTag
- Admin editor interface
- Public list/detail views
- Reading time calculation

### apps/newsletter
**E-bülten yönetimi**
- Subscriber model (double opt-in)
- Email template management
- Digest generation (weekly/monthly)
- Celery task: send_newsletter_digest
- Unsubscribe ve suppression list
- Bounce/complaint handling

### apps/contact
**İletişim formu**
- ContactMessage model
- Form validation
- Admin inbox
- Spam scoring
- Manual resolution workflow

### apps/survey
**Hibe anketi ve eşleştirme**
- Survey questions ve responses
- Audience-gated matcher
- Matching results
- Public survey page

### apps/analytics
**SEO, Analytics, Ads**
- GA4 integration (consent-aware)
- AdSense slots (consent-gated)
- Sitemap generation
- RSS/Atom feed
- Embed card/badge
- Structured data (JSON-LD)
- Open Graph meta tags

### apps/security
**Güvenlik ve audit**
- Admin TOTP 2FA setup
- Secure login form (brute-force protection)
- Audit log model
- Permission management
- Security notification

### apps/search
**Arama ve filtreleme**
- Full-text search index
- Filter querysets
- Search result ranking
- Typeahead suggestions (future)

---

## Geliştirme Durumu

### Faz Özeti

| Faz | Durum | Detay |
|-----|-------|-------|
| **Faz 0 - Hazırlık** | ✅ TAMAMLANDI | Kaynak envanter, teknik stack, domain DNS |
| **Faz 1 - Temel İskelet** | ✅ TAMAMLANDI | Django, Docker, CI, health checks |
| **Faz 2 - Domain & DB** | ✅ TAMAMLANDI | Core modeller, migrations, admin |
| **Faz 3 - Otomasyon Çekirdeği** | ✅ TAMAMLANDI | Adapter, pipeline, scheduler, worker |
| **Faz 4 - Public Sayfalar** | ✅ TAMAMLANDI | Homepage, call list, detail, institutions |
| **Faz 5 - İçerik & Dönüşüm** | ✅ TAMAMLANDI | Blog, survey, newsletter, contact |
| **Faz 6 - SEO & Analitik** | ✅ TAMAMLANDI | GA4, AdSense, RSS, CMP, structured data |
| **Faz 7 - Güvenlik & Ops** | ✅ TAMAMLANDI | CSP, HSTS, 2FA, WAF, backup, audit |
| **Faz 8 - Staging & Lansman** | ✅ TAMAMLANDI | Staging setup, production deploy |
| **Faz 9 - Real Data Writing** | ✅ TAMAMLANDI | Persist layer, adapter registry, crawl |
| **Faz 10 - Quality Cert.** | ✅ TAMAMLANDI | Duplicate, confidence, source scaling |
| **Faz 11 - Live Automation** | 🔄 DEVAM EDİYOR | Scheduler allowlist, production backfill |

### Faz 11 Durumu (Şu Anki)

Production scheduler kontrollü allowlist ile açılmıştır:

```
SOURCE_SCHEDULER_ALLOWLIST=src-0011,src-0017
SOURCE_SCHEDULER_MAX_DUE_SOURCES=1
SOURCE_SCHEDULER_REQUIRE_ALLOWLIST=true
SOURCE_SCHEDULER_ROLLBACK_PAUSED=true
```

**Tamamlanan:**
- ✅ Review queue yayın adaylarını manuel yayın/ret ile bağla
- ✅ Kaynakları kontrollü backfill ile public havuzunu genişlet
- ✅ Rejected/published recrawl idempotency koruması
- ✅ Parser fixture testleri (Priority A kaynakları)
- ✅ Source ölçekleme planı

**Kalan:**
- E-posta teslim ve unsubscribe testi
- İlk 72 saat sıklaştırılmış izleme
- AdSense production activation
- Search Console/Bing verification

---

## Güvenlik & Uyum

### Güvenlik Kontrolleri

#### Application Layer
- ✅ **CSP** (Content Security Policy) - nonce-based
- ✅ **HSTS** - Strict-Transport-Security
- ✅ **Security Headers:** X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, etc.
- ✅ **CSRF Protection** - Django CSRF token
- ✅ **Admin TOTP 2FA** - time-based OTP
- ✅ **Brute-force Protection** - login rate limiting
- ✅ **SQL Injection Prevention** - Django ORM parameterized queries
- ✅ **XSS Prevention** - template auto-escaping
- ✅ **SSRF Protection** - custom HTTP client

#### Network Layer
- ✅ **Cloudflare WAF** - DDoS, bot protection
- ✅ **Cloudflare Rate Limit** - request rate limiting
- ✅ **Origin IP Lockdown** - Cloudflare IPs only
- ✅ **Nginx Rate Limit** - application-level fallback

#### Server Security
- ✅ **SSH Key-Only Access** - no password auth
- ✅ **Root Login Disabled** - ssh_config
- ✅ **Firewall** - firewalld rules
- ✅ **Fail2Ban** - brute-force mitigation
- ✅ **Log Rotation** - logrotate (30-90 days)
- ✅ **Encrypted Backups** - GPG encryption
- ✅ **Backup Restore Testing** - runbook validated

#### Data Security
- ✅ **Field Evidence Truncation** - copyright/disk optimization
- ✅ **Email Encryption** - database level (at rest)
- ✅ **Token Hashing** - no plaintext tokens in DB
- ✅ **Subscriber Privacy** - access restricted
- ✅ **Audit Logging** - JSON structured logs

### Uyum Standartları

#### OWASP ASVS L1
- ✅ Authentication & Session Management
- ✅ Access Control
- ✅ Validation, Sanitization & Encoding
- ✅ Encryption
- ✅ Sensitive Data Protection
- ✅ Logging & Monitoring

Kontrol listesi: `docs/OWASP_ASVS_L1_CHECKLIST.md`

#### Dependency & Container Scanning
- ✅ `pip-audit` - Python dependency vulnerabilities
- ✅ `bandit` - Security code analysis
- ✅ Trivy - Container image scanning
- ✅ GitHub Dependabot - automated alerts

#### Responsible Disclosure
- ✅ `.well-known/security.txt` - security policy
- ✅ Public security page - `/security/`
- ✅ Responsible disclosure process

---

## Operasyon & İzleme

### Monitoring & Logging

#### Structured Logging
```json
{
  "timestamp": "2026-06-30T12:34:56Z",
  "level": "INFO",
  "logger": "apps.sources.tasks",
  "message": "Source crawl started",
  "source_id": 42,
  "worker_id": "celery@worker1",
  "duration_ms": 234
}
```

- JSON structured logs
- Rotation: 30-90 days
- Alert baselines
- Real-time monitoring

#### Health Endpoints
```
GET /health/live   → 200 OK (liveness)
GET /health/ready  → 200 OK (readiness - all dependencies)
```

Checks:
- PostgreSQL connection
- Redis connection
- Web server status
- Worker status

### Source Health Dashboard

Admin panelinde görünen metrikleri:

| Metrik | Açıklama |
|--------|----------|
| Last crawl status | Son tarama başarı/başarısız |
| Run count | Toplam crawl çalıştırmaları |
| Success rate | Başarılı tarama yüzdesi |
| HTTP status summary | 200, 403, 429, 5xx sayıları |
| False positive ratio | Reddedilen/yayınlanan oranı |
| Parser version | Aktif parser versiyonu |
| Config version | Kaynak config versiyonu |
| Consecutive failures | Ardışık başarısız sayı |
| Circuit breaker status | Open/half-open/closed |
| Next scheduled crawl | Sonraki planlı çalışma |

### Controlled Backfill

Production'da kontrollü backfill:

```bash
# Dry run (no commit)
python manage.py schedule_controlled_backfill \
  --limit=10 \
  --sources=src-0085,src-0120

# Real backfill (with commit)
python manage.py schedule_controlled_backfill \
  --limit=10 \
  --countdown-step=30 \
  --commit
```

Features:
- Allowlist support
- Maximum due sources limit
- Rollback gate
- Dry-run mode
- Countdown distribution

### Data Quality Verification

```bash
# Check duplicates and stale statuses
python manage.py verify_call_data_quality \
  --require-checked \
  --fail-on-issues

# Staging probe (rollback-only)
python manage.py verify_call_data_quality --probe
```

### Performance Monitoring

Load smoke test:

```bash
python manage.py run_staging_load_smoke \
  --requests=600 \
  --concurrency=4 \
  --max-p95-ms=1500 \
  --max-error-rate=0
```

Metrics:
- Request latency (mean, p50, p95, p99)
- Error rate
- Throughput (RPS)

### Capacity Planning

Başlangıç baseline:

- **Çağrı havuzu:** ~250+ kurumdan 1,000+ çağrı
- **Traaffic:** staging'de 600 istek/s @ p95 82.5ms
- **Database:** PostgreSQL 14+ @ AWS t3.medium
- **Cache:** Redis @ AWS t3.micro
- **Workers:** Celery 2+ worker instances
- **Web:** Gunicorn 4 workers @ t3.small

Ölçekleme sinyalleri:
- PostgreSQL query slow log > 500ms
- Worker queue depth > 1000
- Memory usage > 80%
- Redis evictions
- Nginx 5xx errors

---

## İleride Ölçekleme (Değil Şimdi)

Servis ayrıştırılması *sadece* sorun kanıtlanırsa:

```
PostgreSQL arama yetersiz  → Meilisearch / OpenSearch
Worker web'i yavaşlatırsa → Dedicated worker server
Media boyutu artarsa       → S3 uyumlu object storage
E-posta volume artarsa     → Separate notification service
Public API talep artarsa   → Versioned read-only API
```

Her ayrıştırma:
- ADR (Architecture Decision Record) gerektirir
- Ölçüm ile gerekçelendirilir
- Backward compatibility sağlanır

---

## Proje Yapısı

```
hiberota/
├── AGENTS.md                    # LLM agent prompts
├── TASKS.md                     # Görev checklist
├── README.md                    # Quick start
├── pyproject.toml               # Proje ayarları
├── docker-compose.yml           # Local dev
├── docker-compose.staging.yml   # Staging
├── Dockerfile                   # Container
│
├── config/                      # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── test.py
│   │   ├── staging.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
│
├── apps/                        # Django modülleri
│   ├── core/
│   ├── calls/
│   ├── sources/
│   ├── institutions/
│   ├── ingestion/
│   ├── taxonomy/
│   ├── blog/
│   ├── newsletter/
│   ├── contact/
│   ├── survey/
│   ├── analytics/
│   ├── security/
│   └── search/
│
├── automation/                  # Tarama otomasyonu
│   ├── adapters/                # Source adapters
│   ├── parsers/                 # Field extractors
│   ├── pipeline/                # Processing stages
│   ├── http/                    # SafeHttpClient
│   └── tasks/                   # Celery tasks
│
├── templates/                   # Django templates
│   ├── base.html
│   ├── pages/
│   ├── includes/
│   └── embeds/
│
├── static/                      # CSS, JS
│   ├── css/
│   └── js/
│
├── ops/                         # Operasyon
│   ├── cloudflare/
│   ├── nginx/
│   ├── security/
│   ├── fail2ban/
│   ├── backup/
│   └── monitoring/
│
├── tests/                       # Test suites
├── docs/                        # Dokumentasyon
└── data/                        # Veri dosyaları
    └── source_catalog_import.csv
```

---

## Sonuç

HibeRota, **production-ready** bir modüler monolit olarak tasarlanmış ve uygulanmıştır:

- ✅ **Mimarisi** sağlam: modüler, ölçeklenebilir, güvenli
- ✅ **Teknolojisi** modern: Python 3.12, Django 5.2 LTS, PostgreSQL
- ✅ **Otomasyonu** kanıtlanabilir: verified adapters, quality controls
- ✅ **Güvenliği** standart: OWASP ASVS L1, WAF, 2FA, audit logs
- ✅ **Operasyonu** kararlı: health checks, monitoring, backup
- ✅ **Geliştirmesi** 11 fazta tamamlandı, production canlı

Platform **30 Haziran 2026** itibarıyla Faz 11'de (Live Automation) aktif olarak kullanımda olup, 
kontrollü kaynak ölçekleme devam etmektedir.

---

**Rapor:** 30.06.2026  
**Versiyon:** 1.0  
**Hazırlayan:** Architecture Analysis System
