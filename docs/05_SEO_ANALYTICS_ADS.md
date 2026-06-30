# SEO, Analitik, Reklam ve Paylaşım Planı

## 1. SEO mimarisi

### Indexlenebilir sayfalar

- Ana sayfa
- Çağrı detayları
- Kurum listesi ve doğrulanmış kurum detayları
- Blog listesi ve blog yazıları
- Temel hedef kitle landing sayfaları
- Ülke/bölge landing sayfaları; yalnızca yeterli özgün içerik varsa
- Yasal ve kurumsal sayfalar

### Varsayılan noindex

- Admin
- İnceleme/draft
- Dahili arama sonuçlarının düşük değerli kombinasyonları
- Sınırsız filtre parametre kombinasyonları
- Preview
- Confirmation/unsubscribe token sayfaları
- Staging
- Hata ve health endpointleri

## 2. URL yapısı

Örnek:

```text
/
/cagrilar/
/cagrilar/{slug}-{short_id}/
/kurumlar/
/kurumlar/{slug}/
/proje-rehberi/
/proje-rehberi/{slug}/
/hibe-anketi/
/iletisim/
/ogrenciler-icin-hibeler/
/akademisyenler-icin-fonlar/
/ulkeler/{country_slug}/
```

Slug değişirse 301 redirect kaydı tutulur. Kullanıcı kontrollü open redirect oluşturulmaz.

## 3. Metadata

Her indexlenebilir sayfada:

- benzersiz title
- benzersiz meta description
- self-referencing canonical
- Open Graph
- uygun sosyal görsel
- robots directive
- breadcrumb
- dil
- güncellenme bilgisi
- kaynak/kurum bağlantısı

Filtre parametreleri canonical stratejisine uyar.

## 4. Sitemap

Sitemap index:

- calls-open
- calls-closed
- institutions
- blog
- landing-pages

Büyük listeler bölünür. `lastmod` yalnızca anlamlı içerik değişikliğinde güncellenir; her crawl run'da yapay olarak değiştirilmez.

## 5. Structured data

Google tarafından desteklenen ve sayfayla gerçekten eşleşen tipler önceliklidir:

- `Organization`
- `WebSite`
- `BreadcrumbList`
- `Article` / `BlogPosting`

Çağrı detaylarında schema.org semantik tipleri kullanılabilir; Google rich result garantisi olarak sunulmaz. Görünmeyen, yanlış veya uydurma structured data eklenmez.

## 6. İçerik kalitesi

Çağrı detay sayfası yalnızca kaynak metni kopyalayan ince sayfa olmamalıdır. Kurallı alanlarla açık düzen:

- kısa özet
- kimler başvurabilir
- ülke/bölge
- kurum
- açılış
- son başvuru
- süre
- destek miktarı
- şartlar
- resmi kaynak
- son doğrulama tarihi
- benzer çağrılar
- ilgili rehber içerikleri

Bilgi kaynakta yoksa tahmin edilmez.

Blog:

- yazar uzmanlığı
- yazar profili
- kaynaklar
- güncelleme tarihi
- editoryal kontrol
- ilgili çağrılar
- görsel alt metni
- özgün içerik

## 7. Core Web Vitals hedefleri

75. persentil mobil hedef:

- LCP <= 2.5 s
- INP < 200 ms
- CLS <= 0.1

Uygulama bütçeleri:

- above-the-fold görseller optimize
- WebP/AVIF uygun kullanım
- width/height zorunlu
- kritik CSS sınırlı
- JavaScript minimal/defer
- Bootstrap yalnızca gerekli bundle
- font self-host veya düşük varyant
- uzun listelerde pagination
- reklam slotlarına sabit alan
- third-party script consent sonrası
- lazy loading, fakat LCP görselinde değil

## 8. Arama motoru operasyonu

- Google Search Console
- Bing Webmaster Tools
- URL inspection
- sitemap submit
- robots testi
- rich result testi
- crawl error takibi
- 404/soft-404 takibi
- canonical takibi
- backlink ve spam takibi
- site migration durumunda 301 haritası

## 9. GA4

Measurement ID:

```text
G-2HHZH6D0QT
```

Uygulama:

- environment değişkeni,
- staging'de ayrı property veya debug,
- consent default denied yaklaşımı,
- kullanıcı onayı sonrası update,
- kişisel veri ve e-posta event parametresine gönderilmez,
- internal admin trafiği hariç tutulur,
- event adları dokümante edilir.

Örnek eventler:

- `search_submitted`
- `filter_applied`
- `call_viewed`
- `official_application_clicked`
- `favorite_added`
- `survey_completed`
- `newsletter_subscribed`
- `blog_call_clicked`
- `embed_copied`

## 10. Consent ve AdSense

- EEA/UK/Swiss kullanıcılar için Google sertifikalı CMP gereksinimi dikkate alınır.
- Cookie ve reklam tercihleri geri alınabilir olmalıdır.
- Analytics ve reklam storage sinyalleri ayrı yönetilir.
- AdSense client ID eksik olduğundan production reklam aktivasyonu bloke edilir.
- Reklam scripti consent ve gerekli kimlik olmadan yüklenmez.
- Reklamlar içerik ile karışacak biçimde tasarlanmaz.
- Otomatik reklamlar CLS ve kullanıcı deneyimi açısından staging'de test edilir.
- Anket/newsletter modalı ile reklam interstitial aynı oturumda çakışmaz.
- Ads.txt, publisher ID geldikten sonra eklenir.

Bu belge hukuki görüş değildir. KVKK, GDPR, ePrivacy ve ticari elektronik ileti metinleri hukuk uzmanı tarafından doğrulanmalıdır.

## 11. Linkleme ve paylaşım

Her çağrıda:

- kalıcı canonical URL
- paylaş butonu
- link kopyala
- Web Share API destekli mobil paylaşım
- LinkedIn/X/Facebook/WhatsApp linkleri
- UTM sadece paylaşım linki üretiminde; canonical temiz kalır
- resmi kaynak linki
- kısa açıklama ve OG görseli

Dış siteler için:

- RSS/Atom veya JSON Feed
- güvenli, salt okunur embed kartı
- "HibeRota'da görüntüle" badge
- embed endpointine ayrı CSP ve rate limit
- iframe veya script embed kullanıcı sayfasına veri yazamaz
- kaynak gösterimi zorunlu
- widget versiyonlama

## 12. Deneysel keşfedilebilirlik

`llms.txt` gibi henüz arama sıralaması garantisi olmayan deneysel dosyalar opsiyonel değerlendirilebilir. Bunlar klasik SEO, structured data, sitemap, özgün içerik ve performansın yerine geçmez.
