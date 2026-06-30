# Test ve Kabul Kriterleri

## 1. Test katmanları

### Unit

- tarih/para normalize
- taxonomy keyword
- status hesaplama
- duplicate fingerprint
- confidence
- survey score
- URL normalize
- SSRF IP kontrolü

### Integration

- PostgreSQL constraint/index
- Celery task idempotency
- source import
- pipeline transaction
- review/publish
- newsletter opt-in/unsubscribe
- admin permission
- cache invalidation

### Parser fixture

Her adapter için.

### End-to-end

- ana sayfadan arama
- filtre
- çağrı detay
- resmi link
- favori
- kurum
- blog
- anket
- iletişim
- newsletter confirmation
- admin review/publish

### Security

- dependency scan
- static analysis
- headers
- CSRF
- XSS
- SSRF
- rate limit
- upload
- auth brute force
- secret scan
- directory traversal
- public file exposure

### Performance

- ana sayfa
- çağrı listesi
- filtre query
- detay
- crawl run
- newsletter batch

## 2. MVP kabul kriterleri

### Veri toplama

- Aynı item tekrar çalıştığında duplicate çağrı oluşmaz.
- Parser alanı bulamazsa uydurma veri üretmez.
- 403/429 kaynağına agresif istek devam etmez.
- Her published çağrıda resmi URL, kurum ve first_seen bulunur.
- Kritik tarih çelişkisi manual review'e düşer.
- Deadline geçmiş çağrı closed görünür.
- Kaynak run sonucu admin'de izlenir.

### Public ürün

- Public üyelik veya login linki yoktur.
- Tüm ana sayfalar mobilde kullanılabilir.
- Filtre state'i URL'de taşınır.
- Favori yalnızca cihazda saklanır.
- Resmi başvuru dış linki çalışır.
- Boş/eksik bilgi doğru mesajla gösterilir.
- Keyboard ile navigasyon mümkündür.
- Form label ve hata ilişkileri erişilebilirdir.

### Blog/admin

- Editor keyfi script ekleyemez.
- Görsel doğrulama ve re-encode edilir.
- Draft public değildir.
- Revision/audit mevcuttur.
- Rol bazlı admin yetkisi çalışır.

### Newsletter/contact

- Double opt-in olmadan aktif gönderim yok.
- Unsubscribe tek tık ve güvenlidir.
- Frequency weekly/monthly korunur.
- E-posta event/log içinde sızmaz.
- Contact spam/rate limit çalışır.
- Admin mesajı görebilir ve durum atayabilir.

### SEO

- Index sayfalarda unique title/canonical.
- Sitemap valid.
- Robots staging'i engeller, production stratejisi doğru.
- Structured data validator hatasız.
- Filter crawl trap yok.
- Open Graph çalışır.
- 404 doğru HTTP status döner.
- Kaldırılmış kayıt uygun 404/410 veya redirect stratejisi kullanır.

### Güvenlik

- `.env`, `.git`, backup, source dosyaları HTTP ile erişilemez.
- DB/Redis dış ağdan erişilemez.
- Admin 2FA aktif.
- DEBUG kapalı.
- HSTS/CSP ve temel headerlar mevcut.
- SSRF test payloadları bloklanır.
- Upload exploit testleri bloklanır.
- Backup restore testi başarılı.
- Critical dependency vulnerability yok.

## 3. Performans hedefleri

Başlangıç hedefleri, staging gerçek ölçümüyle doğrulanır:

- p95 cached public response < 500 ms
- p95 normal liste/detail < 1.5 s
- ana DB query setinde açıklanamayan N+1 yok
- kaynak crawl web requestlerini yavaşlatmaz
- queue gecikmesi saatlik tarama penceresini aşmaz
- Core Web Vitals hedefleri SEO belgesine uygun
- 4 GB RAM altında sürekli swap thrash yok

## 4. Release checklist

- [ ] CI yeşil
- [ ] Migration incelendi
- [ ] Backup alındı
- [ ] Secret scan temiz
- [ ] Staging smoke geçti
- [ ] Accessibility smoke geçti
- [ ] Mobile smoke geçti
- [ ] SEO/canonical kontrolü
- [ ] Source scheduler kontrollü
- [ ] Email sandbox/allowlist kontrolü
- [ ] Rollback image hazır
- [ ] Release note güncel
