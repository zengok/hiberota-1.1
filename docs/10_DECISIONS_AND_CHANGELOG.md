# Mimari Kararlar ve Değişiklik Günlüğü

## ADR-001 — Modüler monolit ve teknik stack

**Durum:** Kabul edildi  
**Belge:** [`adr/ADR-001-technical-stack.md`](adr/ADR-001-technical-stack.md)  
**Karar:** Django 5.2 LTS modüler monolit, Python 3.12, PostgreSQL, Redis/Celery, Bootstrap 5.3, Nginx/Gunicorn, Docker Compose ve Cloudflare.  
**Gerekçe:** 4 GB RAM sunucuda düşük operasyon yükü, SSR SEO, güçlü admin ve Python otomasyon uyumu.  
**Sonuç:** Mikroservis eklenmez; ölçülmüş ihtiyaçta ADR ile ayrıştırılır.

## ADR-002 — PostgreSQL tek kalıcı kaynak

**Durum:** Önerildi  
**Karar:** Automation state dahil üretim kalıcı verisi PostgreSQL'de.  
**Gerekçe:** SQLite + PostgreSQL ayrımı split-brain, backup ve concurrency riski doğurur.  
**Sonuç:** Redis ephemeral; SQLite production dependency değildir.

## ADR-003 — Public kullanıcı hesabı yok

**Durum:** Kabul edilmiş ürün kısıtı  
**Karar:** Public auth/profile yok; admin staff auth var. Favoriler ve anket tercihleri localStorage.  
**Sonuç:** cihazlar arası sync yok; newsletter aboneliği kullanıcı hesabı sayılmaz.

## ADR-004 — MVP'de AI yok

**Durum:** Kabul edilmiş ürün kısıtı  
**Karar:** Veri çıkarma ve eşleştirme deterministik kurallarla.  
**Sonuç:** Gelecekte `EnrichmentProvider` arayüzü eklenebilir; AI çıktısı kaynaksız otomatik publish edilemez.

## ADR-005 — Etik ve uyumlu veri toplama

**Durum:** Kabul edilmiş güvenlik kararı  
**Karar:** API/feed önceliği, robots/terms kontrolü, rate limit/backoff. Anti-bot bypass yok.  
**Sonuç:** Engelli kaynak manual/API-required yapılır.

---

## Changelog formatı

Her release:

```text
## YYYY-MM-DD — vX.Y.Z
Added:
Changed:
Fixed:
Security:
Migration:
Operations:
Rollback:
```

Bu dosya ayrıntılı günlük yerine yüksek seviyeli değişiklikleri taşır. Günlük iş durumu `TASKS.md`, release detayları GitHub PR/release notlarında tutulur.
