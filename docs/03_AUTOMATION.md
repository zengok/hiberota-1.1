# Kaynak Tarama ve Veri İşleme Otomasyonu

## 1. Temel ilke

Amaç "her siteyi ne pahasına olursa olsun kazımak" değildir. Amaç resmi ve izin verilen kaynaklardan sürdürülebilir, düşük yük oluşturan ve doğrulanabilir veri toplamaktır.

Kaynağın güvenlik önlemlerini aşmak, CAPTCHA çözmek, login gerektiren içeriğe izinsiz erişmek, IP/fingerprint gizlemek veya erişim yasağını atlatmak yasaktır.

## 2. Adapter sözleşmesi

Her adaptör aşağıdaki standart arayüze uyar:

```python
class SourceAdapter(Protocol):
    key: str

    def discover(self, context: CrawlContext) -> Iterable[DiscoveredItem]:
        ...

    def fetch_detail(
        self,
        item: DiscoveredItem,
        context: CrawlContext,
    ) -> FetchResult:
        ...

    def parse(
        self,
        result: FetchResult,
        context: CrawlContext,
    ) -> ParsedCall:
        ...
```

Normalize, validate, deduplicate ve publish adapter içine gömülmez; ortak pipeline servisleridir.

## 3. Kaynak erişim önceliği

- Resmi açık API
- Resmi RSS/Atom/JSON feed
- Resmi sitemap
- Resmi CSV/XLSX/XML indirme
- Statik liste ve detay HTML
- JavaScript render zorunlu ve izinli ise Playwright
- Manuel import

API anahtarı gerekiyorsa admin ile güvenli secret olarak tanımlanır.

## 4. Kontrollü HTTP istemcisi

Zorunlu özellikler:

- açık ve dürüst user-agent,
- güvenlik/iletişim e-postası veya bilgi sayfası,
- DNS ve hedef IP doğrulama,
- private/loopback/link-local IP engeli,
- redirect başına yeniden allowlist doğrulama,
- maksimum redirect sayısı,
- connect/read/total timeout,
- maksimum response byte sınırı,
- kabul edilen content-type listesi,
- TLS doğrulama,
- host bazlı concurrency,
- minimum request interval,
- jitter,
- ETag ve Last-Modified,
- sıkıştırma bombası koruması,
- Retry-After desteği,
- exponential backoff,
- circuit breaker,
- 401/403/429 için düşük retry limiti,
- telemetry.

## 5. Robots ve kullanım koşulları

- Kaynak eklenirken robots.txt durumu kaydedilir.
- Robots kuralları bir erişim yetkilendirme sistemi değildir; buna rağmen crawler bunlara uyar.
- Kullanım koşulları açıkça otomasyonu yasaklıyorsa kaynak `manual_only` veya `blocked` yapılır.
- Robots ulaşılamıyorsa politika gereği temkinli varsayım ve düşük hız uygulanır.
- Kaynak sahibi iletişime geçerse hızlı pause/takedown akışı bulunur.

## 6. Hata davranışı

### 429

- `Retry-After` uygula.
- Crawl run'ı saldırgan biçimde tekrar etme.
- Source health skorunu düşür.
- Circuit breaker aç.
- Admin'e yalnızca eşik aşılırsa uyarı gönder.

### 403

- Aynı isteği farklı header/proxy/fingerprint ile atlatmaya çalışma.
- Bir kontrollü tekrar sonrası source'u degraded/blocked yap.
- API, feed veya manuel alternatif araştırma kaydı oluştur.

### 404/410

- Detay URL'sini tekrar doğrula.
- Daha önce yayımlanmış çağrıysa resmi link durumunu işaretle.
- İçerik hemen silinmez; kaynak erişilemiyor uyarısı ve son doğrulama tarihi gösterilebilir.
- 410 kalıcı kaldırmayı güçlü sinyal kabul eder.

### Timeout/5xx

- Sınırlı backoff retry.
- Run idempotent olmalı.
- Aynı item iki worker tarafından işlenmemeli.

## 7. Pipeline

```text
schedule
  -> source lock
  -> discover
  -> normalize discovered URL
  -> early duplicate
  -> fetch
  -> parse
  -> normalize fields
  -> validate
  -> taxonomy rules
  -> duplicate match
  -> confidence
  -> review or publish
  -> evidence
  -> metrics
```

Her aşama ayrı status ve error code üretir.

## 8. Kural tabanlı çıkarım

AI kullanılmadan:

- selector/XPath/JSONPath,
- label-value tabloları,
- regex,
- tarih sözlükleri,
- para birimi sözlükleri,
- ülke/kurum eşleştirme,
- keyword taxonomy,
- sayfa metadata,
- JSON-LD/microdata,
- indirilebilir doküman metadata

kullanılır.

PDF içinde kritik veri varsa:

- kaynağın açık indirme izni olmalı,
- metin katmanı tercih edilmeli,
- OCR yalnızca zorunlu ve kontrollü olmalı,
- çıkarılan veri manual review eşiğini yükseltmelidir.

## 9. Confidence örneği

Toplam 100:

- resmi başlık: 15
- resmi URL: 10
- kurum: 10
- hedef kitle: 10
- açılış/deadline: 20
- amaç/özet: 10
- finansman: 10
- ülke/bölge: 5
- katılım şartı: 5
- parser fixture başarı geçmişi: 5

Örnek karar:

- 85–100 ve kritik çelişki yok: auto publish
- 60–84: review
- 0–59: draft/rejected
- Deadline parse çelişkisi: skordan bağımsız review
- Resmi URL yok: auto publish yok

Eşikler admin ayarı olabilir; değişiklik audit edilir.

## 10. Source catalog Excel importu

Excel doğrudan runtime konfigürasyonu olarak her saat okunmaz.

Akış:

1. Dosya admin veya yönetim komutuyla yüklenir.
2. Şema ve satırlar doğrulanır.
3. Hatalar satır/sütun bazında raporlanır.
4. Geçerli kayıtlar transaction içinde Source tablosuna import edilir.
5. Ön izleme ve değişiklik özeti alınır.
6. Config version artırılır.
7. Orijinal dosya salt okunur arşivlenebilir.

## 11. Parser testleri

Her adaptörde:

- gerçek kaynaktan alınmış ve kullanım açısından uygun sanitize fixture,
- liste parse testi,
- detay parse testi,
- tarih/para normalize testi,
- eksik alan testi,
- selector değişimi testi,
- duplicate testi

bulunur.

Canlı siteye test sürecinde sürekli istek gönderilmez.

## 12. Operasyon dashboardu

Gösterilecekler:

- son run,
- başarı/failure,
- keşfedilen/yeni/güncellenen/review sayıları,
- response süreleri,
- 403/429/5xx,
- consecutive failure,
- parser version,
- config version,
- circuit breaker durumu,
- sonraki planlı çalışma,
- manuel çalıştır/pause,
- son değişen selector notu.
