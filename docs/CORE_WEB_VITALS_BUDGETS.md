# Core Web Vitals Budgets

HibeRota public sayfaları için başlangıç bütçeleri `docs/05_SEO_ANALYTICS_ADS.md` içindeki Core Web Vitals hedeflerine bağlıdır.

## CI kapsamı

Lighthouse CI şu public rotaları ölçer:

- `/`
- `/cagrilar/`
- `/proje-rehberi/`

CI hedefleri:

- LCP <= 2.5 s
- CLS <= 0.1
- TBT <= 200 ms
- Accessibility, best practices ve SEO skorları >= 0.90
- Performance skoru uyarı eşiği >= 0.75

Kaynak bütçeleri `lighthouse-budget.json` içinde tutulur. Lighthouse CI assertions ise `lighthouserc.json` içinde build kırma veya uyarı davranışını belirler.

## Operasyon notları

- Üçüncü taraf scriptler consent sonrası yüklenmelidir.
- Reklam alanları sabit ölçülü kalmalıdır.
- LCP aday görseller lazy-load edilmemelidir.
- Public liste ve detay sayfalarında gereksiz JavaScript eklenmemelidir.
