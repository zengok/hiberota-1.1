# Codex Context Map

Codex her görevde tüm dokümanları okumamalıdır.

| Görev | Öncelikli belge | İkinci belge |
|---|---|---|
| Repo iskeleti/CI | `00_PROJECT_MASTER_PLAN.md` | `07_DEPLOYMENT_RUNBOOK.md` |
| Django app yapısı | `01_ARCHITECTURE.md` | `02_DATA_MODEL.md` |
| Model/migration | `02_DATA_MODEL.md` | `08_TEST_ACCEPTANCE.md` |
| Scraper/adaptör | `03_AUTOMATION.md` | `04_SECURITY.md` |
| Scheduler/Celery | `03_AUTOMATION.md` | `01_ARCHITECTURE.md` |
| Ana sayfa/çağrı UI | `06_UX_UI_FUNCTIONAL_SPEC.md` | `05_SEO_ANALYTICS_ADS.md` |
| Blog/admin | `06_UX_UI_FUNCTIONAL_SPEC.md` | `04_SECURITY.md` |
| Hibe anketi | `06_UX_UI_FUNCTIONAL_SPEC.md` | `02_DATA_MODEL.md` |
| Contact/newsletter | `06_UX_UI_FUNCTIONAL_SPEC.md` | `04_SECURITY.md` |
| SEO/sitemap/schema | `05_SEO_ANALYTICS_ADS.md` | `08_TEST_ACCEPTANCE.md` |
| Analytics/AdSense | `05_SEO_ANALYTICS_ADS.md` | `04_SECURITY.md` |
| Nginx/Cloudflare | `04_SECURITY.md` | `07_DEPLOYMENT_RUNBOOK.md` |
| Backup/deploy | `07_DEPLOYMENT_RUNBOOK.md` | `08_TEST_ACCEPTANCE.md` |
| Kaynak Excel importu | `03_AUTOMATION.md` | `data/SOURCE_CATALOG_SCHEMA.md` |
| Mimari değişiklik | `10_DECISIONS_AND_CHANGELOG.md` | ilgili teknik belge |

## Binary ve büyük dosya kuralı

- Logo/görsel: yalnızca görev için gerekli dosyayı aç.
- UX/UI tasarım: önce dosya adları ve ekran listesi; sonra hedef ekran.
- Excel: önce workbook metadata ve header.
- Crawl fixture: yalnızca ilgili source adapter fixture.
- Log: tüm dosya yerine hata çevresi ve son sınırlı satırlar.
