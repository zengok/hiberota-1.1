# UX/UI ve Fonksiyonel Gereksinimler

## 1. Tasarım ilkeleri

- Güvenilir ve kurumsal
- Akademisyen, öğrenci ve KOBİ için anlaşılır
- Mobil öncelikli
- Yoğun veriyi sade gösteren
- Renk dışında ikon/metin sinyali
- WCAG 2.2 AA hedefi
- Bootstrap grid ve bileşenleri
- Tutarlı spacing/type scale
- Hızlı resmi başvuru aksiyonu
- Her kritik veride açıklayıcı label

Logo ve UX/UI dosyaları kaynak referansıdır. Codex binary tasarım dosyasını yeniden üretmez; bileşen ve token envanteri çıkararak uygular.

## 2. Header ve ortak yapı

Desktop:

- Logo
- Ana Sayfa
- Çağrılar
- Kurumlar
- Proje Rehberi
- Hibe Anketi
- İletişim
- Arama
- Favoriler ikonu yalnızca favori varsa badge ile

Mobile:

- kompakt logo
- arama kısayolu
- menü offcanvas
- yeterli touch target
- favori kısayolu
- focus trap ve ESC davranışı

Footer:

- hızlı linkler
- önemli kategoriler
- güvenlik/gizlilik/cookie/kullanım
- RSS
- güvenlik bildirimi
- Veor Collection marka bağlantısı
- kaynak ve editoryal politika

## 3. Ana sayfa

Sıra:

1. SEO uyumlu tek H1 ve kısa değer önerisi
2. Ana arama
3. Hızlı başlangıç kartları:
   - Öğrenci
   - Akademisyen
   - Araştırmacı
   - Girişimci
   - KOBİ/Firma
   - Kurumsal/Kamu/STK
4. Son Türkiye çağrıları
5. Son dünya çağrıları
6. Favoriler; yalnızca localStorage'da kayıt varsa
7. Yaklaşan son tarihler
8. Öne çıkan kurumlar
9. Proje rehberi içerikleri
10. Açıklayıcı SEO içerik blokları
11. E-bülten CTA
12. Footer

Çağrı satırı/kartı:

- başlık
- kurum
- ülke/bölge
- hedef kitle chipleri
- açılış tarihi
- son tarih
- yakalandığı/ilk görüldüğü zaman
- durum
- detay linki

"Yakalandığı saat" kullanıcıya teknik jargon olmadan "HibeRota'da ilk görülme" şeklinde açıklanır.

## 4. Çağrılar sayfası

Default sıralama: HibeRota'da ilk görülme, yeniden eskiye.

Filtreler:

- metin arama
- ülke
- hızlı Türkiye
- hızlı Avrupa
- bölge
- kurum
- hedef kitle
- sektör
- tema
- program türü
- açık/gelecek/kapanmak üzere/kapalı
- finansman para birimi
- yayın/açılış tarihi
- son başvuru aralığı

Sıralama:

- yeni yakalananlar
- eski yakalananlar
- son tarihi en yakın
- son tarihi en uzak
- açılış tarihi yeni/eski

Mobile filtreler offcanvas olur. Aktif filtreler chip olarak görünür ve tek tek temizlenebilir. Sonuç sayısı gösterilir. URL filtre durumunu taşır; fakat SEO canonical/noindex kuralları uygulanır.

## 5. Çağrı detay

Üst alan:

- başlık
- kurum
- ülke bayrağı yalnızca dekoratif olmayan doğru alt metinle
- durum
- son başvuru countdown yerine kesin tarih öncelikli
- favori
- paylaş
- resmi başvuru

Bilgi kartı:

- kimler başvurabilir
- destek miktarı
- proje süresi
- açılış
- son başvuru
- destekleyen ülkeler
- program türü

İçerik:

- amaç
- kapsam
- uygunluk
- katılım şartları
- finansman
- başvuru süreci
- gerekli belgeler
- resmi bağlantılar
- veri kaynağı ve son doğrulama
- ilgili çağrılar
- ilgili rehberler

Resmi başvuru butonu dış link olduğunu belirtir ve `noopener noreferrer` kullanır.

## 6. Favoriler

Public hesap olmadığı için:

- çağrı ID/slug listesi localStorage'da tutulur,
- PII tutulmaz,
- detaydan ekle/çıkar,
- ana sayfada favoriler alanı sadece doluysa görünür,
- silinen/slug değişen kayıtlar API ile güvenli biçimde çözümlenir,
- kullanıcıya "Bu cihazda saklanır" bilgisi verilir.

İleride hesap sistemi gelirse migration ayrı proje olur.

## 7. Kurumlar

Kurum kartı:

- logo
- ad/kısa ad
- ülke
- aktif açık çağrı sayısı
- toplam yayınlanmış çağrı sayısı
- son güncelleme

Detay:

- kurum açıklaması
- resmi web sitesi
- açık çağrılar
- kapanmış çağrılar
- ülke/tema dağılımı
- veri son güncelleme

Sayılar cache edilir fakat yayın sonrası invalidation yapılır.

## 8. Blog / Proje Rehberi

Kart:

- kapak görseli
- yazar yuvarlak fotoğrafı
- yazar adı
- başlık
- kısa açıklama
- kategori
- tarih/okuma süresi

Admin editörü:

- title, slug, excerpt
- cover, alt text, caption/source
- yazar
- rich text block
- heading/list/link/quote/image
- preview
- draft/schedule/publish
- SEO title/description
- canonical
- related calls
- revision/audit

Script, iframe ve keyfi HTML eklenmez. Embedler allowlist ile yönetilir.

## 9. Hibe anketi

İlk ziyaret:

- sayfayı anında kaplayan zorlayıcı modal yok,
- birkaç saniye veya ilk etkileşim sonrası,
- atla seçeneği,
- bir oturumda newsletter popup ile çakışmaz,
- tekrar gösterim sıklığı localStorage ile sınırlandırılır.

Sorular:

- rol/meslek
- kurum türü
- ülke/bölge
- sektör
- proje konusu
- proje aşaması
- ortaklık durumu
- bütçe aralığı
- başvuru zamanı
- deneyim

Eşleştirme açıklanabilir kural puanı ile yapılır. Sonuçlarda "neden uygun" gösterilir. AI kullanılmaz.

## 10. İletişim

Alanlar:

- ad soyad
- e-posta
- konu
- açıklama
- gizlilik onayı
- spam koruması

Mesaj admin inbox'a düşer. E-posta bildiriminde tam hassas mesaj yerine admin linki tercih edilir.

Alt marka alanı:

- Veor Collection logosu
- "HibeRota, Veor Collection tarafından geliştirilen bir dijital üründür." benzeri kontrollü metin
- `veorcollection.com` dış bağlantısı
- iki marka hiyerarşisini karıştırmayan görsel ayrım

## 11. E-bülten popup

- sağ alt desktop, mobile bottom sheet
- aynı oturumdaki anket modalıyla çakışmaz
- haftalık/aylık seçim
- e-posta
- açık izin metni
- double opt-in
- kapatma ve frequency cap
- kullanıcı reddederse kısa sürede tekrar gösterilmez
- unsubscribe her e-postada

## 12. Hata ve boş durumlar

- Filtre sonucu yok: önerilen filtre temizleme
- Favori yok: alan tamamen gizli veya favoriler sayfasında açıklayıcı empty state
- Kaynak link bozuk: son doğrulama ve alternatif kurum sayfası
- Deadline bilinmiyor: tahmini tarih gösterilmez
- Sistem yoğun: güvenli 429/503
- Kapanmış çağrı: arşiv olarak erişilebilir, resmi uyarı belirgin
