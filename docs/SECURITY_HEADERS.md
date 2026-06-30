# Security Headers

HibeRota public sayfalarında temel güvenlik başlıkları `apps.security.headers.SecurityHeadersMiddleware` ile merkezi uygulanır.

## Uygulanan başlıklar

- `Content-Security-Policy`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `X-Permitted-Cross-Domain-Policies: none`
- Django production ayarlarıyla `Strict-Transport-Security`, `X-Content-Type-Options` ve `X-Frame-Options`

Embed endpointleri kendi izole CSP politikasını korur ve cross-origin iframe kullanımını kırmamak için `Cross-Origin-Resource-Policy` başlığını site geneli değerle zorlamaz.

## CSP kaynakları

Başlangıç politikası self-first çalışır. İzinli dış kaynaklar:

- Bootstrap CDN: `https://cdn.jsdelivr.net`
- GA4: `https://www.googletagmanager.com`
- Analytics connect: `https://www.google-analytics.com`, `https://region1.google-analytics.com`
- Consent sonrası AdSense loader: `https://pagead2.googlesyndication.com`
- Ad frame: `https://googleads.g.doubleclick.net`
- HTTPS CMP script origin'i, yalnızca `CMP_SCRIPT_URL` geçerli HTTPS URL ise

Inline scriptler nonce ile çalışır. Yeni inline event handler eklenmez; form davranışları external JavaScript ile bağlanır.

## Production notu

`DJANGO_SECURE_HSTS_PRELOAD` varsayılanı güvenli şekilde `false` tutulur. Preload yalnızca subdomain kapsamı doğrulandıktan sonra açılır.
