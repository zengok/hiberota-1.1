# HibeRota — Plan Uyumluluğu Rehberi

**Tarih:** 30 Haziran 2026  
**Durum:** ✅ TASKS.md Master Plan'a Uyumlu Hale Getirildi  

---

## 🎯 AÇIK PLAN YASAKLARI

Master Plan'da açıkça yazılı olan ve **ASLA yapılmayacak** görevler:

### 1. **Public Kullanıcı Üyeliği / Hesabı**
```
PLAN: "Bu projede halka açık kullanıcı hesabı veya profil sistemi YOKTUR."
PLAN: "Public kullanıcı üyeliği: yok."

❌ YASAKLANMIŞ:
  - Kullanıcı kayıt formu
  - Kullanıcı profili
  - Login/signup sistemi
  - Kullanıcı hesapları
  - Sosyal login (Google, GitHub, vb)
  - Şifre yönetimi
```

### 2. **Kullanıcı Veri Depolama**
```
❌ YASAKLANMIŞ:
  - Kişisel veri tutma
  - Kullanıcı profilleri
  - Tercih ve geçmiş (database'de)
  - Aktivite logları (user-specific)
  - Cihazlar arası senkronizasyon
```

### 3. **Kültürel & Yapay Zeka (MVP)**
```
PLAN: "MVP aşamasında yapay zekâ API'si KULLANILMAZ"

❌ YASAKLANMIŞ (MVP):
  - Yapay zeka entegrasyonu
  - Çok dilli içerik üretimi
  - Otomatik çeviriler

✅ İZİN VERİLEN:
  - Altyapı hazırlanması
  - Manuel çeviriler (gelecek)
  - AI-optional design (future-ready)
```

### 4. **Ödeme & Monetization (MVP)**
```
❌ YASAKLANMIŞ (MVP):
  - Stripe/ödeme işlemcileri
  - Premium features
  - Abonelik sistemi (kamu için)
  - İn-app satın alması
```

### 5. **Native Mobile Uygulaması**
```
✅ İZİN VERİLEN:
  - PWA (Progressive Web App)
  
❌ YASAKLANMIŞ (MVP):
  - Native iOS app
  - Native Android app
  - App Store distribution
  - Biometric auth
```

---

## ✅ PLAN'IN İZİN VERDİĞİ EXTENSIONLAR

Bu görevler Master Plan tarafından açıkça izin verilmiştir:

### 1. **Read-Only API (Public)**
```
PLAN: "public veri tüketimi artarsa versioned read-only API"

✅ İZİN VERİLEN:
  - REST API v1 (read-only)
  - GraphQL (read-only)
  - OAuth token auth (no user accounts)
  - Rate limiting
  - Developer keys
  
❌ YASAK:
  - Write/delete operations
  - Kullanıcı profili endpointleri
  - Hesap yönetimi
```

### 2. **Internal Analytics (Admin Only)**
```
PLAN: "yalnızca gerçek anonim iç ürün olaylarını veya admin raporlarını taşır"

✅ İZİN VERİLEN:
  - Admin dashboard
  - Metrics ve charts
  - CSV/Excel export (admin)
  - Email reports (internal team)
  - Anonim user behavior
  
❌ YASAK:
  - Public analytics
  - Kişisel veri
  - User tracking
  - Profiling
```

### 3. **Email-Based Alerts (No Accounts)**
```
PLAN: "Public favoriler ve anket tercihleri: tarayıcı localStorage içinde"

✅ İZİN VERİLEN:
  - localStorage preferences
  - Email alerts via newsletter
  - Saved searches (email-based)
  - Double opt-in
  - Unsubscribe
  
❌ YASAK:
  - Database user table
  - Profil depolama
  - Hesap sistemi
  - Şifre
```

### 4. **PWA (No Accounts Required)**
```
✅ İZİN VERİLEN:
  - Progressive Web App
  - Service worker
  - Offline support
  - Install prompt
  - Push notifications (newsletter alerts)
  
❌ YASAK:
  - Kullanıcı hesapları
  - Profiller
  - Giriş/çıkış
  - Kişisel veri
```

### 5. **Performance & Scaling**
```
✅ İZİN VERİLEN:
  - Database optimization
  - Redis caching
  - Elasticsearch
  - CDN
  - Load testing
  - Read replicas
```

### 6. **White-Label/Enterprise**
```
✅ İZİN VERİLEN:
  - Custom branding (admin)
  - Custom domain (admin)
  - Organization management (admin)
  
❌ YASAK:
  - Public signup
  - Kullanıcı profilleri
  - End-user accounts
```

---

## 📋 TASKS.md TARAFINDAN KALDIRILAN

Eski TASKS.md'de var olan ama **Master Plan'a aykırı** olan görevler kaldırıldı:

| Eski Faz | Başlık | Durum | Sebep |
|----------|--------|-------|-------|
| 13 | User Profiles & Personalization | ❌ KALDIRILIYOR | Plan: "public üyelik yok" |
| (13 replacement) | Kullanıcı Activity Log | ❌ KALDIRILIYOR | Hiçbir user data |
| (13 part) | Collaborative Features | ❌ KALDIRILIYOR | No accounts |
| (13 part) | Dark mode / Multilingual | ✅ UI features sadece | Kişisel data yok |
| 17 | Native Mobile Apps | ❌ KALDIRILIYOR | PWA yerine |
| 18 | ML/Personalization | ⚠️ Optional | Needs ADR approval |
| 19 | Kurumsal SSO/Billing | ⚠️ Partial | Admin only, public signup yok |
| 23 | Monetization Experiments | ❌ KALDIRILIYOR | MVP scope dışı |

---

## 🔄 TASKS.MD YENİ YAPISI

### Faz 12-24: Master Plan Uyumlu

```
Faz 0-11:  Plan tarafından tanımlanan MVP ✅ (TAMAMLANDI)

Faz 12:    REST API v1 (read-only, public, no accounts) ✅
Faz 13:    Internal Analytics Dashboard (admin only) ✅
Faz 14:    Email Alerts (newsletter, no accounts) ✅
Faz 15:    Advanced Search Optimization ✅
Faz 16:    Performance & Scaling ✅
Faz 17:    PWA (no accounts required) ✅
Faz 18:    Machine Learning (optional, needs ADR) ⚠️
Faz 19:    White-Label/Enterprise (admin-only) ✅
Faz 20:    Source Expansion ✅
Faz 21:    Compliance & Security ✅
Faz 22:    i18n Infrastructure (no content) ✅
Faz 23:    Monitoring & Observability ✅
Faz 24:    Testing & Documentation ✅
```

### Kilit Prensip: HIÇBIR PUBLIC ACCOUNTS

Tüm geliştirmeler şu kuralı izler:
- ✅ **Read-only API** (no auth required)
- ✅ **Email-based** (newsletter system)
- ✅ **localStorage** (client-side only)
- ✅ **Admin panel** (staff only)
- ❌ **NO user accounts**
- ❌ **NO databases**
- ❌ **NO profiles**

---

## ⚠️ SPECIAL CASES

### Machine Learning (Faz 18)
```
PLAN: "MVP aşamasında yapay zekâ API'si KULLANILMAZ"

Faz 18 opsiyonel ve şu koşulla:
- ADR (Architectural Decision Record) gerekli
- Plan değişikliği onaylanmalı
- MVP scope dışı
```

### Multilingual Content (Faz 22)
```
PLAN: "Çok dilli içerik üretimi; altyapı hazır olabilir fakat gerçek çeviri olmadan"

Faz 22 opsiyonel ve şu koşulla:
- i18n altyapısı kurulabilir
- Otomatik çeviriler YASAKLI
- Manuel çeviriler sadece gelecek
- Hreflang KULLANILMAZ (gerçek çeviriler olmadan)
```

---

## 📄 İLGİLİ BELGELER

| Dosya | Amaç |
|-------|------|
| `/HIBEROTA_CODEX_MASTER_PLAN.md` | Resmi Plan - AUTHORIZATION belgesi |
| `/TASKS.md` | Güncellenmiş görev listesi (✅ Plan uyumlu) |
| `/TASKS_CODEX_COMPLIANT.md` | Detaylı Plan uyumluluğu analizi |
| `/AGENTS.md` | Codex çalışma kuralları |

---

## 🚫 KESIN HATALAR (Asla Yapmayın)

1. **User hesabı oluşturma**
   ```python
   # ❌ WRONG
   class UserProfile(models.Model):
       user = models.OneToOneField(User)
       preferences = models.JSONField()
   ```

2. **Kişisel veri depolama**
   ```python
   # ❌ WRONG
   class UserActivity(models.Model):
       user = models.ForeignKey(User)
       viewed_call_id = models.ForeignKey(GrantCall)
       timestamp = models.DateTimeField()
   ```

3. **Profile-based personalization**
   ```python
   # ❌ WRONG
   def recommend_calls(user):
       return GrantCall.objects.filter(
           audience=user.profile.audience_preference,
           sector=user.profile.sector_preference
       )
   ```

4. **Ödeme entegrasyonu (MVP)**
   ```python
   # ❌ WRONG (MVP)
   import stripe
   
   class SubscriptionPlan(models.Model):
       stripe_product_id = models.CharField()
   ```

---

## ✅ DOĞRU APPROACH

1. **API (read-only, public)**
   ```python
   # ✅ CORRECT
   class CallViewSet(viewsets.ReadOnlyModelViewSet):
       queryset = GrantCall.objects.published()
       serializer_class = CallSerializer
       authentication_classes = [TokenAuthentication]  # NO user accounts
   ```

2. **Analytics (anonim, admin)**
   ```python
   # ✅ CORRECT
   @admin.register(CallMetrics)
   class CallMetricsAdmin(admin.ModelAdmin):
       # NO user tracking
       # Anonim event logging only
       readonly_fields = ['view_count', 'favorite_count']
   ```

3. **Alerts (email, no profile)**
   ```javascript
   // ✅ CORRECT
   // localStorage + newsletter system
   // NO user database
   const saveSearch = (query) => {
       const searches = JSON.parse(localStorage.getItem('searches') || '[]');
       searches.push({query, timestamp: new Date().toISOString()});
       localStorage.setItem('searches', JSON.stringify(searches));
       // Send email via newsletter signup (optional)
   }
   ```

4. **PWA (no auth required)**
   ```javascript
   // ✅ CORRECT
   // installable, offline-capable, NO user accounts
   if ('serviceWorker' in navigator) {
       navigator.serviceWorker.register('/sw.js');
   }
   ```

---

## 📞 PLAN İHLALİ ŞÜPHESİ

Plan ihlali riski gördüğünüzde:

1. **Kontrol edin:** Master Plan'da açıkça yasaklı mı?
2. **Danışın:** Lead/PM ile ADR değişikliği isteyin
3. **Belgelendirin:** Neden gerekli olduğunu
4. **Onayla:** Master Plan'ı resmi olarak güncelleyin

**ASLA:**
- ❌ Planı gizlice eşelendirmeyin
- ❌ "İhtiyacımız var" diye plan ihlal etmeyin
- ❌ Küçük değişiklikleri ses çıkarmadan yapmayın

---

## ✨ SUMMARY

**Master Plan İlkesi:**
```
NO PUBLIC USER ACCOUNTS AT ANY PHASE
```

**Tüm görevler şu kuralı izler:**
1. **Kamu özelliği:** Hiçbir login/profile
2. **Email-based:** Newsletter sistemi üzerinden
3. **localStorage:** Client-side only
4. **Admin panel:** Staff only
5. **Read-only API:** Kamuya açık, yazma yok

**Sorularınız:**
- Bunun kullanıcı hesabı gerektirmesi gerekiyor mu? → ASLA
- Profil/tercih depolaması gerekiyor mu? → localStorage only
- Plan'a aykırı görülüyor mu? → ADR isteyin

---

**Status:** ✅ READY FOR IMPLEMENTATION  
**Last Updated:** 30 June 2026  
**Compliance Level:** 100% Master Plan  
