# HibeRota Task List - Codex Master Plan Uyumlu

**Önemli:** Bu dosya Master Plan'a tam uyumlu görevleri içerir.

---

## ⚠️ PLAN DÖNÜŞÜMLERİ

### Kaldırılması Gerekenler (Plan'a Aykırı)
- ❌ Faz 13: User Profiles & Personalization → **KALDIRILIYOR**
- ❌ Kamu kullanıcıları için hesap sistemi → **YOKTUR (plan uyarı)**
- ❌ Kullanıcı profilleri → **YOKTUR (plan uyarı)**
- ❌ Kişisel veri depolama → **YOKTUR (plan uyarı)**

### Plan Tarafından Resmi Olarak Yasaklanan
1. **Public kullanıcı üyeliği**
2. **Kullanıcı profili sistemi**
3. **Ödeme sistemleri** (MVP)
4. **Mobil uygulama** (PWA'ya kadar)
5. **Yapay zeka API entegrasyonu** (MVP)
6. **Kamu yazma API'si** (read-only API sadece)
7. **Çok dilli içerik üretimi**

### Plan'ın İzin Verdiği Extensionlar
1. ✅ **Read-only API** (REST/GraphQL)
2. ✅ **Internal Analytics** (Admin panel)
3. ✅ **Performance Optimization**
4. ✅ **PWA** (hesap olmadan)
5. ✅ **Email-based Alerts** (public olmayan)
6. ✅ **White-label** (ama public signup yok)
7. ✅ **GDPR/Compliance** tools

---

## 📋 REVISED TASK PHASES (Plan Uyumlu)

### ✅ Faz 0-8: Codex Master Plan (TAMAMLANDI)

Tüm görevler tamamlandı ve plan uyumlu.

### 📌 Faz 9+: Plan Uyumlu Ek Geliştirmeler

---

## **Faz 12 — REST API v1 (Read-Only, Public**

**Plan Uyumu:** ✅ İzin verilen "public veri tüketimi artarsa versioned read-only API"

```
- [ ] Read-only API endpoints (/calls, /institutions, /sources)
- [ ] API authentication (token-based, developer keys)
- [ ] Rate limiting (no account creation required)
- [ ] OpenAPI/Swagger documentation
- [ ] Python SDK examples
- [ ] NO public membership/signup
- [ ] NO user data collection
- [ ] NO personalization via profiles
```

**Kısıtlamalar (Plan'a Uygun):**
- Yalnızca READ işlemleri
- Hiçbir yazma/delete işlemi
- Hiçbir kullanıcı profili/veri
- Herkese açık (hesap yok)

---

## **Faz 13 — Internal Analytics Dashboard (Admin Only)**

**Plan Uyumu:** ✅ İzin verilen "admin raporları"

Faz 13'teki "User Profiles" yerine **INTERNAL ANALYTICS** kullanılacak.

```
- [ ] Admin metrics dashboard
- [ ] Kaynak performans charts
- [ ] User behavior analytics (anonim only)
- [ ] CSV/Excel export (admin only)
- [ ] Email reports (internal team)
- [ ] NO public user tracking
- [ ] NO personal data collection
- [ ] NO user accounts
```

**Kısıtlamalar (Plan'a Uygun):**
- Yalnızca admin erişimi
- Anonim istatistikler
- Hiçbir kişisel veri
- Hiçbir kullanıcı profili

---

## **Faz 14 — Email Alerts (Published via Newsletter, No Profiles)**

**Plan Uyumu:** ✅ İzin verilen "newsletter"

```
- [ ] Email-based saved search alerts (via newsletter system)
- [ ] No user account required
- [ ] localStorage + email confirmation flow
- [ ] Weekly/monthly digest emails
- [ ] Double opt-in (existing newsletter)
- [ ] One-click unsubscribe
- [ ] NO user database
- [ ] NO profiles or personal data
```

**Kısıtlamalar (Plan'a Uygun):**
- Hiçbir hesap sistemi
- Yalnızca email-based alerts
- Mevcut newsletter sistemi üzerine kurul
- Hiçbir profil/personalization

---

## **Faz 15 — Advanced Search Optimization**

**Plan Uyumu:** ✅ İzin verilen "PostgreSQL araması"

```
- [ ] Full-text search optimization
- [ ] Query performance tuning
- [ ] EXPLAIN ANALYZE optimization
- [ ] Autocomplete suggestions (no user data)
- [ ] Search analytics (anonim only)
- [ ] Better filter combinations
- [ ] NO personalized results
- [ ] NO user tracking
```

---

## **Faz 16 — Performance & Scaling**

**Plan Uyumu:** ✅ İzin verilen "ölçeklendirme"

```
- [ ] Database read replicas (future)
- [ ] Elasticsearch (if needed)
- [ ] CDN optimization
- [ ] Image lazy loading
- [ ] Query caching
- [ ] Worker optimization
- [ ] Load testing
```

---

## **Faz 17 — PWA (Progressive Web App, No Accounts)**

**Plan Uyumu:** ✅ İzin verilen "mobil" ama "public üyelik yok"

```
- [ ] PWA manifest
- [ ] Service worker (offline support)
- [ ] Install prompt (mobile)
- [ ] Push notifications (newsletter-based, no user IDs)
- [ ] Offline mode
- [ ] NO user accounts required
- [ ] NO profiles
- [ ] NO personal data
```

**Kısıtlamalar (Plan'a Uygun):**
- Hiçbir hesap/profil sistemi
- Push notifications = newsletter alerts only
- Yalnızca localStorage
- Hiçbir user tracking

---

## **Faz 18 — Machine Learning (Optional, Not MVP)**

**Plan Uyumu:** ⚠️ Sorgulanabilir - Plan MVP'de yasaklıyor, isteğe bağlı ise ✅

```
YALNIZCA PLAN TARAFINDAN ONAYLANDI DURUMUNDA:

- [ ] Grant matching model (NOT critical)
- [ ] Anomaly detection (data quality)
- [ ] No ML-based personalization for public
- [ ] NO user data collection
- [ ] NO profiles
```

**Koşul:** Master Plan'a ADR ile değişiklik gerekli.

---

## **Faz 19 — White-Label/Enterprise (No Public Accounts)**

**Plan Uyumu:** ✅ Varsayılan admin paneline göre ✅

```
- [ ] White-label branding
- [ ] Custom domain
- [ ] Organization management (admin only)
- [ ] NO public signup
- [ ] NO user profiles
- [ ] NO accounts for end-users
- [ ] Admin-only customization
```

**Kısıtlamalar (Plan'a Uygun):**
- Yalnızca admin kustomizasyonu
- Hiçbir public accounts
- Hiçbir kullanıcı profili

---

## **Faz 20 — Source Expansion**

**Plan Uyumu:** ✅ İzin verilen "kaynakları ölçeklendir"

```
- [ ] 20+ source adapters
- [ ] Headless browser support (optional)
- [ ] PDF extraction (controlled)
- [ ] Multi-language sources
- [ ] Source quality scoring
- [ ] NO user data collection
```

---

## **Faz 21 — GDPR & Compliance**

**Plan Uyumu:** ✅ İzin verilen (güvenlik bölümü)

```
- [ ] GDPR compliance (data minimization)
- [ ] Privacy policy
- [ ] Cookie consent (CMP)
- [ ] Data subject rights
- [ ] Security audit
- [ ] NO user personal data (there are no users!)
```

**Basit:** Public üyelik olmadığından GDPR kapsamı minimal.

---

## **Faz 22 — Internationalization (Infrastructure Only)**

**Plan Uyumu:** ⚠️ Plan yasaklıyor - "Çok dilli içerik üretimi YOKTUR"

```
PLAN TARAFINDAN YASAKLANDI:
- ❌ Çok dilli içerik üretimi
- ❌ Otomatik çeviriler

İZİN VERİLEN:
- ✅ Infrastructure prep (i18n setup)
- ✅ Manual çeviriler (gelecek)
- ✅ Regional landing pages (özgün content varsa)
```

---

## **Faz 23 — Monitoring & Observability**

**Plan Uyumu:** ✅ İzin verilen (operasyon)

```
- [ ] Advanced monitoring dashboard
- [ ] Performance metrics
- [ ] Error tracking
- [ ] Log aggregation
- [ ] Alert rules
- [ ] NO user tracking
```

---

## **Faz 24 — Testing & Documentation**

**Plan Uyumu:** ✅ İzin verilen (quality)

```
- [ ] End-to-end tests
- [ ] Performance regression tests
- [ ] Security audit
- [ ] API documentation
- [ ] Runbooks
- [ ] NO user feature tests (no users!)
```

---

## 🚫 REMOVED/REJECTED PHASES

### ❌ Faz 13 (Old): User Profiles & Personalization
**Sebep:** Master Plan açıkça yasaklıyor - "Public kullanıcı üyeliği: yok"

### ❌ Public User Accounts (Any Phase)
**Sebep:** Plan mimarisi buna izin vermiyor

### ❌ User Tracking/Profiling
**Sebep:** Plan'da hesap sistemi yok, localStorage sadece client-side

### ❌ Ödeme Systemi
**Sebep:** Plan MVP scope dışı

### ❌ Mobil Uygulama (Native)
**Sebep:** Plan "PWA evet, native app hayır" diyor

---

## 📊 COMPLIANT PHASE STRUCTURE

```
Faz 0-8:   Plan tarafından tanımlanan MVP ✅
Faz 12:    Read-only API (public, no accounts) ✅
Faz 13:    Internal Analytics (admin only) ✅
Faz 14:    Email Alerts (no accounts) ✅
Faz 15:    Search Optimization ✅
Faz 16:    Performance & Scaling ✅
Faz 17:    PWA (no accounts required) ✅
Faz 18:    ML (optional, needs approval) ⚠️
Faz 19:    White-Label (admin-only) ✅
Faz 20:    Source Expansion ✅
Faz 21:    Compliance & Security ✅
Faz 22:    i18n Infrastructure (no content) ✅
Faz 23:    Monitoring & Observability ✅
Faz 24:    Testing & Documentation ✅
```

---

## ✅ KEY PRINCIPLES (Plan Enforced)

1. **NO PUBLIC USER ACCOUNTS** at any phase
2. **NO USER PROFILING** - localStorage only for favorites
3. **NO PERSONAL DATA STORAGE** for public users
4. **ADMIN PANEL ONLY** for admin features
5. **READ-ONLY API** for public developers
6. **EMAIL-BASED** notifications (no accounts)
7. **ANONIM ONLY** for any analytics/tracking
8. **NO AUTHENTICATION** required for public features

---

## 🔴 REJECTED Faz 13

Old Faz 13 (User Profiles & Personalization) must be replaced with **Faz 13 — Internal Analytics Dashboard** because:

1. Master Plan says: "Public kullanıcı üyeliği: yok"
2. Master Plan says: "Yalnızca yetkili personel için güvenli yönetim paneli"
3. Personalization without accounts = contradiction

---

**Last Updated:** 30 June 2026  
**Compliance:** ✅ Master Plan'a tam uyumlu  
**Status:** READY FOR IMPLEMENTATION (Codex Safe)
