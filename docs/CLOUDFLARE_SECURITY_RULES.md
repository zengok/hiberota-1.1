# Cloudflare Security Rules

Bu belge HibeRota production yayını için Cloudflare WAF, rate limit ve DDoS kural setini tarif eder. Gerçek Cloudflare zone ID, account ID, API token veya origin IP bilgisi repoya yazılmaz.

Makine okunabilir referans: `ops/cloudflare/waf-rate-limit-rules.json`

## Ön koşullar

- DNS proxy turuncu bulut ile aktif.
- SSL/TLS modu Full (Strict).
- Origin sertifikası ve HTTPS doğrulanmış.
- Production smoke testleri tamamlanmış.
- False-positive takibi için Cloudflare Security Events ve uygulama logları izlenebilir.

## Zorunlu korumalar

- Cloudflare Managed Ruleset aktif.
- OWASP Core Ruleset aktif.
- HTTP DDoS Managed Ruleset aktif.
- Bot protection uyumlu modda aktif.
- `/admin` trafiğinde managed challenge.
- Hassas dosya yolları için block kuralı.
- `/admin`, `/iletisim`, `/bulten`, `/hibe-anketi`, `/api/` ve `/embed/` için ayrı rate limit.

## Rate limit davranışı

Başlangıç eşikleri normal kullanımın üstünde tutulmuştur. Üretimde Security Events, 429 oranı ve form dönüşüm kaybı izlenmeden eşikler agresifleştirilmez.

| Kural | Eşik | Aksiyon |
| --- | ---: | --- |
| Global public browsing | 600 istek / 60 sn / IP | managed challenge |
| Admin | 20 istek / 60 sn / IP | managed challenge |
| İletişim POST | 5 istek / 600 sn / IP | managed challenge |
| Bülten POST | 8 istek / 600 sn / IP | managed challenge |
| Hibe anketi POST | 12 istek / 600 sn / IP | managed challenge |
| API/embed | 120 istek / 60 sn / IP | managed challenge |

## Uygulama sırası

1. Managed WAF ve DDoS kurallarını log/managed challenge modunda etkinleştir.
2. Hassas dosya block kuralını etkinleştir.
3. Rate limit kurallarını managed challenge ile etkinleştir.
4. 24 saat Security Events, 403/429, form submit ve admin login oranlarını izle.
5. False-positive yoksa yüksek riskli kuralları block aksiyonuna yükseltmeyi değerlendir.

## Rollback

Sorun görülürse önce ilgili custom WAF veya rate limit kuralını disable et. Managed Ruleset tamamını kapatmak yerine problemli rule ID için skip/exception kullan.

## Kapsam dışı

Bu görev Cloudflare üzerinde gerçek deploy yapmaz, API token kullanmaz ve origin IP kısıtlamasını uygulamaz. Origin erişimini Cloudflare IP'leriyle sınırlandırma ayrı Faz 7 maddesidir.
