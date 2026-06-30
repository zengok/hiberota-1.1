# HibeRota Uygulama Görevleri

Bu dosya kısa tutulmalıdır. Tamamlanan maddeler tarih ve PR numarasıyla işaretlenir.

## Faz 0 — Hazırlık

- [x] Proje klasöründeki logo, UX/UI ve Excel kaynak dosyalarının envanterini çıkar. (2026-06-25, PR yok: local skeleton)
- [x] Kaynak Excel'inin şema uygunluğunu kontrol et; orijinal dosyayı değiştirme. (2026-06-25, PR yok: uyumsuzluk raporu `docs/SOURCE_CATALOG_VALIDATION.md`)
- [x] Teknik stack ADR-001'i onayla. (2026-06-25, PR yok: `docs/adr/ADR-001-technical-stack.md`)
- [x] Staging ve production domain/DNS planını tanımla. (2026-06-25, PR yok: `docs/DOMAIN_DNS_PLAN.md`)
- [ ] AdSense publisher/client kimliğini güvenli ortam değişkeni olarak temin et.
- [ ] Admin iletişim ve güvenlik bildirim e-posta adreslerini belirle.

## Faz 1 — Temel iskelet

- [x] Django proje iskeleti ve modüler uygulamaları oluştur. (2026-06-25, PR yok: local skeleton)
- [x] Docker Compose local ortamı oluştur. (2026-06-25, PR yok: local skeleton)
- [x] PostgreSQL, Redis, web, worker ve beat healthcheck ekle. (2026-06-25, PR yok: local skeleton)
- [x] Ortam bazlı settings yapısını oluştur. (2026-06-25, PR yok: local skeleton)
- [x] Ruff, mypy, pytest, bandit ve pip-audit ekle. (2026-06-25, PR yok: local skeleton)
- [x] GitHub Actions CI oluştur. (2026-06-25, PR yok: local skeleton)
- [x] Nginx geliştirme/staging konfigürasyonunu oluştur. (2026-06-25, PR yok: local skeleton)
- [x] `/health/live` ve `/health/ready` uçlarını oluştur. (2026-06-25, PR yok: local skeleton)

## Faz 2 — Domain ve veritabanı

- [x] Ülke, kurum, kaynak, çağrı ve sınıflandırma modellerini oluştur. (2026-06-25, PR yok: initial Django models/migrations)
- [x] Çağrı tarih ve durum hesaplama servisini oluştur. (2026-06-25, PR yok: `apps/calls/services.py`)
- [x] Duplicate fingerprint ve veritabanı constraintlerini oluştur. (2026-06-25, PR yok: fingerprint helper and DB constraints)
- [x] Kaynak kanıtı/provenance modelini oluştur. (2026-06-25, PR yok: `apps/ingestion/models.py`)
- [x] PostgreSQL full-text ve trigram indekslerini oluştur. (2026-06-25, PR yok: PostgreSQL search index migration)
- [x] Admin temel CRUD ekranlarını oluştur. (2026-06-25, PR yok: Django admin registrations)

## Faz 3 — Otomasyon çekirdeği

- [x] Source adapter interface oluştur. (2026-06-25, PR yok: `automation/adapters/contracts.py`)
- [x] Excel kaynak kataloğu import doğrulayıcısı oluştur. (2026-06-25, PR yok: `apps/sources/catalog_validation.py`)
- [x] HTTP istemcisine robots, rate limit, timeout, retry ve SSRF koruması ekle. (2026-06-25, PR yok: safe HTTP client foundation)
- [x] Pipeline aşamalarını oluştur. (2026-06-25, PR yok: pipeline stage contract)
- [x] Review queue ve confidence kurallarını oluştur. (2026-06-25, PR yok: review model and confidence rules)
- [x] Scheduler, worker ve crawl lock mekanizmasını oluştur. (2026-06-25, PR yok: Celery schedule and crawl lock)
- [x] En az üç farklı kaynak tipi için örnek adaptör geliştir. (2026-06-25, PR yok: api/feed/html examples)
- [x] Fixture tabanlı parser testlerini ekle. (2026-06-25, PR yok: example adapter fixtures)
- [x] Kaynak sağlık dashboardunu oluştur. (2026-06-25, PR yok: admin health summary/status)

## Faz 4 — Public sayfalar

- [x] Ortak layout, header, footer ve navigasyon. (2026-06-26, PR yok: Django template layout skeleton)
- [x] Ana sayfa. (2026-06-26, PR yok: public homepage with model-backed sections)
- [x] Çağrılar listeleme ve filtreleme. (2026-06-26, PR yok: public call list filters)
- [x] Çağrı detay sayfası. (2026-06-26, PR yok: public call detail page)
- [x] Kurumlar ve kurum detay sayfası. (2026-06-26, PR yok: public institution list/detail pages)
- [x] Favoriler localStorage akışı. (2026-06-26, PR yok: localStorage favorites flow)
- [x] Mobil filtre offcanvas ve erişilebilir bileşenler. (2026-06-26, PR yok: accessible mobile filter offcanvas)
- [x] 404, 410, 429 ve 500 hata sayfaları. (2026-06-26, PR yok: public noindex error pages)

## Faz 5 — İçerik ve dönüşüm

- [x] Blog/yazar modelleri ve admin editörü. (2026-06-26, PR yok: blog author/post models and admin editor)
- [x] Blog liste ve detay sayfası. (2026-06-26, PR yok: public blog list and detail pages)
- [x] Hibe anketi ve eşleştirme motoru. (2026-06-26, PR yok: public survey page and audience-gated matcher)
- [x] İletişim formu ve admin mesaj kutusu. (2026-06-26, PR yok: contact form with admin inbox and spam controls)
- [x] E-bülten double opt-in ve abonelik tercihleri. (2026-06-26, PR yok: email-only double opt-in subscriptions)
- [x] Haftalık/aylık e-posta üretim görevleri. (2026-06-26, PR yok: idempotent newsletter digest tasks)
- [x] Unsubscribe ve suppression list. (2026-06-26, PR yok: one-click unsubscribe with suppression list)
- [x] Veor Collection marka alanı. (2026-06-26, PR yok: public brand area)

## Faz 6 — SEO, analitik ve paylaşım

- [x] Metadata, canonical, robots ve sitemap index. (2026-06-26, PR yok: robots and sitemap endpoints)
- [x] Breadcrumb ve desteklenen structured data. (2026-06-26, PR yok: JSON-LD structured data)
- [x] Open Graph ve sosyal paylaşım. (2026-06-26, PR yok: OG meta and share action)
- [x] RSS/Atom veya JSON Feed. (2026-06-26, PR yok: latest calls RSS feed)
- [x] Güvenli embed kartı/badge. (2026-06-26, PR yok: CSP-isolated call embed badge)
- [x] GA4 `G-2HHZH6D0QT` consent-aware entegrasyonu. (2026-06-26, PR yok: consent-gated GA4 loader)
- [x] Google sertifikalı CMP ve Consent Mode. (2026-06-26, PR yok: CMP-ready Consent Mode v2 bridge)
- [x] AdSense alanları; kimlik gelmeden reklamı aktif etme. (2026-06-26, PR yok: consent-gated ad slots)
- [x] Search Console ve Bing Webmaster doğrulama hazırlığı. (2026-06-26, PR yok: env-driven verification meta)
- [x] Core Web Vitals bütçeleri ve Lighthouse CI. (2026-06-26, PR yok: Lighthouse CI budgets)

## Faz 7 — Güvenlik ve operasyon

- [x] Cloudflare WAF/rate limit/DDoS kuralları. (2026-06-26, PR yok: Cloudflare security rules reference)
- [x] Origin erişimini Cloudflare IP'leriyle sınırla. (2026-06-26, PR yok: Cloudflare origin lockdown reference)
- [x] SSH key-only, root login kapalı, firewall ve fail2ban. (2026-06-28, PR yok: production host üzerinde `deploy` key-only erişim, root/password SSH reddi ve fail2ban doğrulandı)
- [x] CSP, HSTS ve diğer security headers. (2026-06-27, PR yok: nonce-based CSP and security headers)
- [x] Admin TOTP 2FA ve brute-force koruması. (2026-06-27, PR yok: secure admin login form)
- [x] Backup, şifreleme ve restore testi. (2026-06-27, PR yok: encrypted backup and restore test runbook)
- [x] Log rotation, monitoring ve alarm. (2026-06-27, PR yok: JSON logs and monitoring alarm baseline)
- [x] `.well-known/security.txt` ve public güvenlik politikası. (2026-06-27, PR yok: responsible disclosure page)
- [x] OWASP ASVS L1 kontrol listesi. (2026-06-27, PR yok: ASVS 5.0.0 L1 checklist)
- [x] Bağımlılık ve container taraması. (2026-06-27, PR yok: dependency review and Trivy CI scan)

## Faz 8 — Staging, veri ve lansman

- [x] Kaynak kataloğunu staging'e import et. (2026-06-28, PR yok: `staging.hiberota.com` ayrı stack kuruldu, `data/source_catalog_import.csv` ile 249 source import edildi)
- [x] Kontrollü backfill yap. (2026-06-28, PR yok: staging'de 10 kaynaklık kontrollü backfill kuyruğu çalıştırıldı; otomatik geniş scheduler tetiklemesini önlemek için `SOURCE_SCHEDULER_ENABLED=false` guard doğrulandı)
- [x] Duplicate ve kapanış durumlarını doğrula. (2026-06-28, PR yok: `verify_call_data_quality --require-checked` boş staging çağrı tablosunu bloke ediyor; `--probe` rollback-only staging DB kontrolü duplicate ve expired->closed uyumsuzluğunu doğruladı)
- [x] Yük ve soak testi. (2026-06-28, PR yok: staging `run_staging_load_smoke` ile 600 istek/concurrency 4, 0 hata, p95 82.5 ms; production health doğrulandı)
- [ ] E-posta teslim ve unsubscribe testi.
- [x] DNS/SSL/redirect/canonical doğrulaması. (2026-06-27, PR yok: canlı `hiberota.com` SSL, www redirect ve canonical doğrulandı)
- [x] Üretim deploy ve smoke test. (2026-06-27, PR yok: eski Node stack yedeklendi/durduruldu, Django stack canlıya alındı)
- [ ] İlk 72 saat sıklaştırılmış izleme.

## Faz 9 — Otomasyonun gerçek veri yazma akışı

- [x] `ParsedCall` verisini transaction içinde `GrantCall`, taxonomy ilişkileri, evidence ve review kayıtlarına yazan persist katmanını oluştur. (2026-06-28, PR yok: `automation.pipeline.persistence.persist_parsed_call` ve testleri eklendi)
- [x] Adapter registry oluştur; kaynak `adapter_key` değerini gerçek adapter sınıfına bağla. (2026-06-28, PR yok: exact ve katalog suffix tabanlı adapter çözümleme eklendi)
- [x] `crawl_source` Celery taskını adapter discover/fetch/parse/persist pipelineına bağla. (2026-06-28, PR yok: task registry, kontrollü HTTP fetch, parse ve persist akışına bağlandı; network mock'lu test eklendi)
- [x] `CrawlRun` ve `CrawlItem` modellerini ekle; run metriklerini ve hata kodlarını kalıcılaştır. (2026-06-29, PR yok: ingestion run/item modelleri, admin yüzeyi, migration ve `crawl_source` metrik yazımı eklendi)
- [x] Duplicate stratejisinin source external_id, canonical URL ve semantic fingerprint katmanlarını pipeline içinde uygula. (2026-06-29, PR yok: persist katmanı source+external_id, canonical URL ve institution/title/deadline fingerprint sırasıyla mevcut çağrıyı güncelliyor)
- [x] Confidence ve validation sonucuna göre auto-publish veya review queue kararını uygula. (2026-06-29, PR yok: parsed call validation eklendi; official URL/canonical/title eksikleri ve deadline conflict auto-publish'i bloke edip review reason üretiyor)
- [x] HTTP istemcisini gerçek crawl pipelineında kullan; robots, SSRF, timeout, retry ve response-size sınırlarını doğrula. (2026-06-29, PR yok: crawl task SafeHttpRequest konfigürasyonunu source config_json'dan retry istemcisine taşıyor; robots, allowlist, timeout ve response-size sınırları testlendi)
- [x] En az bir gerçek kaynak tipi için fixture tabanlı uçtan uca crawl testi ekle. (2026-06-29, PR yok: sanitize static HTML fixture dosyasıyla discover/fetch/parse/persist hattı uçtan uca test edildi)
- [x] Kontrollü staging backfill ile gerçek çağrı yazımını doğrula ve kalite raporunu çalıştır. (2026-06-29, PR yok: staging stack güncellendi, `ingestion.0003` migrate edildi, 3 kaynaklık backfill kuyruğunda 1 gerçek çağrı yazıldı; `verify_call_data_quality --require-checked --fail-on-issues` geçti, 2 kaynak HTTPError ile review/operasyon takibine kaldı)
- [x] Otomasyon metriklerini admin/source health ekranına bağla. (2026-06-29, PR yok: Source admin listesine son crawl durumu, run sayaçları ve HTTP özetleri eklendi; `source_automation_metrics` testleri geçti)
- [x] Katalog taxonomy seed ve hedef kitle eşlemesini production akışına bağla. (2026-06-29, PR yok: `seed_taxonomy` komutu eklendi, `ngo`/`sme`/`researcher` canonical audience verisi seed edildi, UNDEF çağrısında `STK` chip'i canlıda doğrulandı)
- [x] Manuel yayınlanan çağrının güvenli recrawl sonrası review'a düşmesini engelle. (2026-06-29, PR yok: yalnızca `missing_dates` sebebi kalan mevcut published çağrılar published korunuyor; `src-0011` recrawl sonrası canlıda published + `STK` doğrulandı)
- [x] Production kontrollü backfill ile public çağrı havuzunu genişlet. (2026-06-29, PR yok: `src-0014`, `src-0015`, `src-0017` robots allowed doğrulandı ve kontrollü backfill çalıştı; 7 rehber/kapalı kayıt reddedildi, Global Innovation Fund iklim fonu yayınlandı, canlı public çağrı sayısı 2 oldu)
- [x] Rejected/published kararlarının recrawl idempotency korumasını tamamla. (2026-06-29, PR yok: mevcut rejected kayıtlar recrawl sonrası rejected kalıyor; validation issue olmayan manuel published kayıtlar published korunuyor; `src-0017` canlı recrawl ile doğrulandı)

## Faz 10 — Otomasyon kalite sertleştirme ve kaynak ölçekleme

- [x] Statik HTML detay link keşfinde rehber/genel bilgi false-positive filtrelerini sıkılaştır. (2026-06-29, PR yok: IDRC/GIF rehber slug filtreleri eklendi; `src-0017` canlı recrawl 4 detail yerine 1 gerçek fon detail işledi, `src-0014` rehber linki elendi)
- [x] Kaynak sayfalarındaki kapalı/açık durum ve deadline alanlarını parser katmanında yapılandırılabilir çıkar. (2026-06-29, PR yok: Static HTML adapter `source_status` ve deadline regex/default field extraction ekledi; IDRC canlı recrawl kapalı çağrılarda `closed` + deadline kanıtı yazdı, açık ANeSA çağrısı deadline ile review'a düştü)
- [x] Review queue için kapalı çağrı, rehber sayfa ve yayınlanabilir çağrı ayrımını raporlayan yönetim komutu ekle. (2026-06-29, PR yok: `report_review_queue` yönetim komutu kapalı kaynak, rehber sayfa, yayın adayı ve manuel inceleme ayrımıyla eklendi; hedef testler ve kuru rapor geçti)
- [x] Production’da ikinci kontrollü backfill batch’i için robots allowed, statik HTML ve düşük riskli kaynak adaylarını seçip çalıştır. (2026-06-29, PR yok: `src-0018` ve `src-0023` robots allowed + active HTML kaynakları dry-run sonrası kontrollü Celery backfill ile çalıştırıldı; ikisi de HTTP 200 ve hata yok, mevcut parser yeni çağrı üretmedi)
- [x] Source health metriklerine false-positive oranı ve publish/reject oranı görünürlüğü ekle. (2026-06-29, PR yok: Source admin metriklerine `pub/rej/rev/fp` sayıları ve publish/reject/false-positive oranları eklendi; production’da `src-0014` ve `src-0017` canlı metrikleri doğrulandı)
- [x] Scheduler’ı production’da açmadan önce kaynak allowlist, limit ve rollback kapısını tanımla. (2026-06-29, PR yok: `SOURCE_SCHEDULER_ALLOWLIST`, `SOURCE_SCHEDULER_MAX_DUE_SOURCES`, `SOURCE_SCHEDULER_REQUIRE_ALLOWLIST` ve `SOURCE_SCHEDULER_ROLLBACK_PAUSED` kapıları eklendi; production’da scheduler kapalıyken `schedule_due_sources()` 0 doğrulandı)

## Faz 11 — Canlı ürün kabul kapıları ve kontrollü otomasyon açılışı

- [x] Review queue’daki yayın adaylarını resmi kaynak, deadline, hedef kitle ve zorunlu alan kanıtlarıyla manuel yayın veya ret kararına bağla. (2026-06-29, PR yok: ID 19 ANeSA çağrısı resmi IDRC sayfasında open + 2026-08-24 03:59 UTC deadline ile doğrulandı; researcher/Afrika/health/research/grant taxonomy bağlandı, review publish edildi ve public listede göründü)
- [x] Production scheduler allowlist’ini yalnızca kanıtlı düşük riskli kaynaklarla başlat; limit, rollback flag ve ilk beat çevrimi doğrulamasını yap. (2026-06-29, PR yok: production scheduler `src-0011,src-0017` allowlist ve `SOURCE_SCHEDULER_MAX_DUE_SOURCES=1` ile açıldı; ilk beat çevrimi `sources.schedule_due_sources` çalıştırıp 0 döndü, yeni geniş `CrawlRun` oluşmadı)
- [x] İlk 72 saat sıklaştırılmış izleme raporunu gerçek production metrikleriyle tamamla; site health, queue, crawl, kaynak hata oranı ve public çağrı kalitesini kapsa. (2026-06-29, PR yok: `docs/FIRST_72_HOUR_MONITORING_REPORT.md` canlı health, queue, crawl, source health, review queue ve public call quality snapshot’ı ile eklendi)
- [ ] E-posta domaini ve teslim altyapısı hazır olduğunda double opt-in, digest ve unsubscribe uçtan uca testini production-safe alıcı listesiyle doğrula.
- [ ] Admin iletişim ve güvenlik bildirim e-posta adreslerini ortam değişkenleri ve public güvenlik metinleriyle uyumlu hale getir.
- [ ] AdSense publisher/client kimliği sağlandığında CMP/consent kapısı altında production reklam aktivasyonunu doğrula.
- [ ] Search Console ve Bing doğrulama meta değerlerini gerçek ortam değişkenleriyle yayına alıp sitemap/feed indekslenebilirliğini kontrol et.
- [x] Kaynak ölçekleme için üçüncü controlled backfill aday listesini, parser fixture ihtiyacı ve false-positive riskine göre önceliklendir. (2026-06-29, PR yok: `docs/THIRD_CONTROLLED_BACKFILL_CANDIDATES.md` eklendi; `src-0085` ve `src-0120` fixture-first Priority A, `src-0020` ve `src-0076` yüksek risk Priority B olarak sınıflandı, crawl başlatılmadı)
- [x] Priority A kaynakları için fixture tabanlı parser testlerini ekle. (2026-06-30, PR yok: `src-0085` Eureka ve `src-0120` UKRI sanitize liste/detay fixture testleri eklendi; `www` host eşleşmesi, rehber/status filtreleri ve label-value status/deadline parse doğrulandı)
- [x] Priority A kaynakları için production commit'siz controlled backfill dry-run planını doğrula. (2026-06-30, PR yok: `src-0085` ve `src-0120` active kaynakları 2 kaynaklık dry-run planında doğrulandı; `--commit` kullanılmadı)
- [x] Priority A kaynakları için sınırlı production backfill ve review temizliğini tamamla. (2026-06-30, PR yok: `src-0120` ve `src-0085` commit'li backfill çalıştı; oluşan 10 rehber/filtre/program false-positive review kaydı rejected yapıldı, review queue ve kalite kontrol temiz)

## ⚠️ IMPORTANT: Master Plan Uyumluluğu

**MASTER PLAN YASAKLARI:**
- ❌ Public kullanıcı üyeliği/hesabı: YOKTUR
- ❌ Kullanıcı profilleri: YOKTUR
- ❌ Kişisel veri depolama: YOKTUR (public users)
- ❌ Ödeme sistemleri: MVP scope dışı
- ❌ Yapay zeka (MVP): Optional
- ❌ Native mobil uygulaması: PWA yerine

**İZİN VERİLENLER:**
- ✅ Read-only API (public, no accounts)
- ✅ Internal Analytics (admin only)
- ✅ Email alerts (via newsletter, no accounts)
- ✅ PWA (no accounts required)
- ✅ White-label (admin-only)

Detay: `TASKS_CODEX_COMPLIANT.md` dosyasını okuyun.

## Faz 12 — REST API v1 (Read-Only, Public)

**Plan Uyumu:** ✅ İzin verilen "versioned read-only API"

- [ ] Read-only API endpoints (/calls, /institutions, /sources)
- [ ] API authentication (token-based, developer keys)
- [ ] Rate limiting (hesap oluşturma gerektirmeyen)
- [ ] OpenAPI/Swagger documentation
- [ ] Python SDK examples
- [ ] Webhook support (read-only events)
- [ ] NO public membership/signup
- [ ] NO user data collection
- [ ] NO personalization

## Faz 13 — Internal Analytics Dashboard (Admin Only)

**Plan Uyumu:** ✅ İzin verilen "admin raporları"

- [ ] Admin metrics dashboard (charts, trends)
- [ ] Kaynak performans analytics
- [ ] Erişim analytics (anonim, hiçbir kişisel veri)
- [ ] Data export (CSV/Excel, admin only)
- [ ] Email reports (internal team only)
- [ ] Search analytics
- [ ] NO public user tracking
- [ ] NO user profiles
- [ ] NO personal data

## Faz 14 — Email-Based Alerts (Newsletter Integration)

**Plan Uyumu:** ✅ İzin verilen "newsletter"

- [ ] Email alerts (saved searches, newsletter via)
- [ ] No account required
- [ ] localStorage + email confirmation flow
- [ ] Weekly/monthly digest emails
- [ ] Double opt-in
- [ ] One-click unsubscribe
- [ ] NO user database
- [ ] NO profiles

## Faz 15 — Advanced Search Optimization

**Plan Uyumu:** ✅ İzin verilen "PostgreSQL araması"

- [ ] Full-text search optimization
- [ ] Query performance tuning
- [ ] EXPLAIN ANALYZE optimization
- [ ] Autocomplete suggestions
- [ ] Search analytics (anonim only)
- [ ] Filter combinations
- [ ] NO personalized results
- [ ] NO user tracking

## Faz 16 — Performance & Scaling

**Plan Uyumu:** ✅ İzin verilen "ölçeklendirme"

- [ ] Database query optimization
- [ ] Redis cache enhancement
- [ ] Elasticsearch (optional)
- [ ] CDN integration
- [ ] Image optimization
- [ ] Frontend optimization
- [ ] Database connection pooling
- [ ] Read replicas (future)
- [ ] Load testing

## Faz 17 — PWA (Progressive Web App, No Accounts)

**Plan Uyumu:** ✅ İzin verilen "mobil" (hesap yok)

- [ ] PWA manifest
- [ ] Service worker (offline)
- [ ] Install prompt (mobile)
- [ ] Push notifications (newsletter alerts only)
- [ ] Offline mode
- [ ] NO user accounts
- [ ] NO profiles
- [ ] NO personal data

## Faz 18 — Machine Learning (Optional, Needs Approval)

**Plan Uyumu:** ⚠️ Sorgulanabilir - Master Plan MVP'de yasaklıyor

- [ ] Grant matching (optional, needs ADR)
- [ ] Anomaly detection (data quality)
- [ ] NO personalization for public
- [ ] NO user data collection
- [ ] NO profiles

**Koşul:** Master Plan'dan onay gerekli.

## Faz 19 — White-Label/Enterprise (Admin-Only)

**Plan Uyumu:** ✅ İzin verilen (admin panel)

- [ ] White-label branding (admin)
- [ ] Custom domain (admin)
- [ ] Organization management (admin only)
- [ ] NO public signup
- [ ] NO user profiles/accounts
- [ ] Admin-only customization

## Faz 20 — Source Expansion

**Plan Uyumu:** ✅ İzin verilen "kaynakları ölçeklendir"

- [ ] 20+ source adapters
- [ ] Headless browser (optional)
- [ ] PDF extraction (controlled)
- [ ] Multi-language sources
- [ ] Source quality scoring
- [ ] NO user data collection

## Faz 21 — Compliance & Security

**Plan Uyumu:** ✅ İzin verilen (güvenlik)

- [ ] GDPR compliance (data minimization)
- [ ] Privacy policy
- [ ] Cookie consent (CMP)
- [ ] Data subject rights
- [ ] Security audit
- [ ] NO user personal data (no users!)

## Faz 22 — i18n Infrastructure (No Content)

**Plan Uyumu:** ⚠️ Plan yasaklıyor - "Çok dilli içerik üretimi YOKTUR"

- [ ] i18n infrastructure setup
- [ ] Multi-currency support
- [ ] Regional filtering
- [ ] Timezone handling
- [ ] NO automated translations
- [ ] Manual translations only (future)

## Faz 23 — Monitoring & Observability

**Plan Uyumu:** ✅ İzin verilen (operasyon)

- [ ] Advanced monitoring dashboard
- [ ] Performance metrics
- [ ] Error tracking
- [ ] Log aggregation
- [ ] Alert rules
- [ ] NO user tracking

## Faz 24 — Testing & Documentation

**Plan Uyumu:** ✅ İzin verilen (quality)

- [ ] End-to-end tests
- [ ] Performance regression tests
- [ ] Security audit
- [ ] API documentation
- [ ] Runbooks
- [ ] NO user feature tests (no users!)
