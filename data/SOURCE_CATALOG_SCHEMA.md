# Kaynak Kataloğu Excel Şeması

## 1. Amaç

Proje klasöründeki Excel; taranacak kurum ve portalların kontrollü başlangıç kataloğudur. Runtime sırasında her saat Excel okunmaz. Excel doğrulanarak PostgreSQL `Source` kayıtlarına import edilir.

## 2. Zorunlu sayfa

Önerilen sayfa adı: `sources`

## 3. Sütunlar

| Sütun | Zorunlu | Örnek | Açıklama |
|---|---:|---|---|
| `source_key` | Evet | `tubitak_calls` | Değişmeyen unique kimlik |
| `institution_name` | Evet | `TÜBİTAK` | Kurum |
| `institution_short_name` | Hayır | `TÜBİTAK` | Kısa ad |
| `country_code` | Evet | `TR` | ISO alpha-2 |
| `region_code` | Hayır | `EU` | İç sınıflandırma |
| `source_name` | Evet | `TÜBİTAK Duyurular` | Kaynak adı |
| `base_url` | Evet | `https://...` | Ana domain |
| `listing_url` | Evet | `https://.../calls` | Liste URL |
| `source_type` | Evet | `html` | api/feed/sitemap/html/headless/manual |
| `adapter_key` | Evet | `tubitak_html_v1` | Kod adapter kimliği |
| `crawl_interval_minutes` | Evet | `60` | Minimum periyot |
| `language_codes` | Evet | `tr,en` | Virgüllü |
| `audience_hints` | Hayır | `researcher,sme` | Taxonomy key |
| `robots_checked_at` | Hayır | `2026-06-25` | Kontrol tarihi |
| `robots_status` | Evet | `allowed` | allowed/restricted/unknown |
| `terms_status` | Evet | `reviewed` | reviewed/restricted/unknown |
| `api_docs_url` | Hayır | | Resmi API dokümanı |
| `rss_feed_url` | Hayır | | Resmi feed |
| `contact_url` | Hayır | | Kaynak iletişim |
| `enabled` | Evet | `true` | Import sonrası aktiflik |
| `notes` | Hayır | | İnsan notu |
| `config_json` | Hayır | `{...}` | Şeması doğrulanan non-secret config |

## 4. Yasak içerik

Excel içinde bulunmamalı:

- parola
- API secret
- cookie/session
- proxy credential
- admin giriş bilgisi
- kişisel veri
- CAPTCHA bypass bilgisi
- kaynak güvenliğini aşmaya yönelik header/fingerprint

Secret gerekli ise source key üzerinden environment secret manager'a bağlanır.

## 5. Import doğrulamaları

- unique source_key
- geçerli URL/scheme
- country code
- enum değerleri
- interval alt limiti
- config JSON schema
- domain allowlist
- duplicate institution/source
- robots/terms uyarıları
- headless kaynakların açık gerekçesi
- devre dışı kaynağın scheduler'a girmemesi

## 6. Değişiklik yönetimi

Import öncesi diff:

- eklenecek
- güncellenecek
- pasife alınacak
- adapter değişecek
- interval değişecek
- güvenlik/uyum uyarısı

İnsan onayı sonrası transaction uygulanır. Dosya hash'i ve import eden admin audit log'a yazılır.
