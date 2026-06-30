# Veri Modeli ve İş Kuralları

## 1. Ana varlıklar

### Country

- `code` — ISO 3166-1 alpha-2, unique
- `name_tr`
- `name_en`
- `region_code`
- `is_eu_member`
- `is_europe`
- `is_active`

### Institution

- `name`
- `slug`
- `short_name`
- `institution_type`
- `country`
- `website_url`
- `logo`
- `description`
- `is_verified`
- `is_active`

### Source

- `institution`
- `name`
- `base_url`
- `listing_url`
- `source_type`: api/feed/sitemap/html/headless/manual
- `adapter_key`
- `status`: active/paused/degraded/blocked/retired/manual_only
- `crawl_interval_minutes`
- `robots_status`
- `terms_status`
- `contact_url`
- `last_success_at`
- `last_failure_at`
- `consecutive_failures`
- `health_score`
- `config_json`
- `config_version`

Selector veya parser config'i JSON olabilir fakat doğrulanmış schema kullanılır. Secret içeremez.

### GrantCall

Kimlik:

- `id`
- `title`
- `slug`
- `source`
- `institution`
- `external_id`
- `official_url`
- `canonical_source_url`
- `fingerprint`

İçerik:

- `summary`
- `purpose`
- `eligibility_text`
- `conditions_text`
- `duration_text`
- `funding_text`
- `application_process_text`
- `contact_text`

Yapısal alanlar:

- `source_published_at`
- `application_open_at`
- `deadline_at`
- `deadline_timezone`
- `first_seen_at`
- `last_seen_at`
- `last_verified_at`
- `duration_min_months`
- `duration_max_months`
- `funding_min`
- `funding_max`
- `currency`
- `funding_rate_percent`

Durum:

- `workflow_status`: discovered/review/published/rejected/archived
- `availability_status`: upcoming/open/closing_soon/closed/unknown
- `confidence_score`
- `is_featured`
- `published_at`
- `closed_at`

Kaynak güveni:

- `title_confidence`
- `deadline_confidence`
- `eligibility_confidence`
- `funding_confidence`

### Taxonomy

Ayrı yönetilebilir tablolar:

- AudienceType
- Sector
- Theme
- ProgramType
- OrganizationSize
- Region
- KeywordRule

Örnek audience:

- student
- graduate_student
- academic
- researcher
- entrepreneur
- startup
- sme
- company
- ngo
- municipality
- public_institution
- consortium

GrantCall ile çoktan çoğa ilişki kullanılır.

### CrawlRun

- `source`
- `trigger_type`: schedule/manual/retry/backfill
- `status`
- `started_at`
- `finished_at`
- `discovered_count`
- `fetched_count`
- `created_count`
- `updated_count`
- `review_count`
- `duplicate_count`
- `failed_count`
- `http_status_summary`
- `error_code`
- `error_summary`
- `worker_id`
- `config_version`

### CrawlItem

- `crawl_run`
- `source_url`
- `normalized_url`
- `external_id`
- `content_hash`
- `status`
- `attempt_count`
- `http_status`
- `parser_version`
- `raw_metadata_json`
- `grant_call`
- `error_code`

### FieldEvidence

Her kritik alan için:

- `grant_call`
- `field_name`
- `source_url`
- `source_excerpt`
- `selector_or_path`
- `fetched_at`
- `content_hash`
- `parser_version`
- `confidence`

Tam sayfanın sınırsız kopyası saklanmaz. Kanıt metni telif, disk ve kişisel veri ilkelerine göre kısa tutulur.

### ReviewItem

- `grant_call` veya `crawl_item`
- `reason_code`
- `severity`
- `assigned_to`
- `status`
- `resolution`
- `created_at`
- `resolved_at`

### Subscriber

- `email_normalized`
- `status`: pending/active/unsubscribed/bounced/complained/suppressed
- `frequency`: weekly/monthly
- `country/region preference` — isteğe bağlı
- `audience preferences` — isteğe bağlı
- `consent_at`
- `consent_ip_hash`
- `confirmation_token_hash`
- `confirmed_at`
- `unsubscribed_at`
- `source`

E-posta düz metin olarak iş gereği tutulur; erişim ve loglama sınırlandırılır. Token düz metin tutulmaz.

### ContactMessage

- `full_name`
- `email`
- `subject`
- `message`
- `status`
- `created_at`
- `handled_at`
- `admin_notes`
- `spam_score`

### Blog

- Author
- BlogPost
- BlogCategory
- BlogTag

BlogPost:

- title, slug, excerpt, body
- cover image, alt text
- author
- status
- publish/update time
- SEO title/description
- canonical override
- reading time
- source/disclosure fields

## 2. Durum hesaplama

`availability_status` kullanıcı girdisiyle rastgele değiştirilmez; tarih ve override kuralıyla hesaplanır.

Örnek:

```text
deadline bilinmiyor              -> unknown
open_at gelecekte                -> upcoming
deadline geçmiş                  -> closed
deadline <= now + threshold      -> closing_soon
diğer                            -> open
```

Resmi kaynak açıkça kapattıysa manuel override mümkündür. Override audit log üretir.

## 3. Duplicate stratejisi

Sıra:

1. Aynı source + external_id
2. Normalize edilmiş canonical URL
3. Institution + normalize title + deadline exact hash
4. Trigram benzerliği + institution + tarih toleransı
5. Manual review

Otomatik birleştirme yalnızca yüksek güvenli eşleşmede yapılır. Farklı yıllara ait aynı program çağrıları birleştirilmez.

## 4. Arama

Arama dokümanı aşağıdakilerden oluşturulur:

- title yüksek ağırlık
- institution name
- short name
- summary
- purpose
- eligibility
- keywords
- country
- audience
- theme
- program type

Türkçe ve İngilizce normalize desteği planlanır. Arama sorgusu uzunluğu ve token sayısı sınırlandırılır.

## 5. İndeksler

Minimum:

- `deadline_at`
- `first_seen_at`
- `published_at`
- `workflow_status`
- `availability_status`
- `institution_id`
- `source_id`
- `country relations`
- `fingerprint` unique/partial
- FTS GIN
- title trigram GIN/GiST
- subscriber email unique normalized

İndeksler gerçek sorgu planlarıyla kontrol edilir; her alana indeks eklenmez.

## 6. Veri saklama

Önerilen başlangıç:

- Crawl run özetleri: uzun süre
- Başarılı raw response gövdeleri: varsayılan saklama yok veya çok sınırlı
- Hata response örnekleri: maskelenmiş, 7–30 gün
- Field evidence: çağrı yayında olduğu sürece veya politika süresi
- App log: 30–90 gün
- Security log: ihtiyaca göre daha uzun ve erişim kısıtlı
- Contact mesajı: işleme ve yasal gerekliliğe göre
- Unsubscribed/suppression: yeniden gönderimi engelleyecek minimum kayıt

Kesin süreler gizlilik politikası ve hukuk incelemesiyle sabitlenir.
