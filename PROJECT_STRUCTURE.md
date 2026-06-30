# 📁 HibeRota Project Structure - Organized View

**Tarih:** 30 Haziran 2026  
**Durum:** ✅ Organized & Clean

---

## 🎯 Root Directory (Essential Files Only)

```
hiberota_codex_project_pack/
│
├── 📋 CORE PROJECT FILES
│   ├── manage.py                    # Django management script
│   ├── pyproject.toml               # Project metadata
│   ├── README.md                    # Quick start guide
│   ├── TASKS.md                     # ⭐ All tasks & phases (11→24)
│   └── AGENTS.md                    # LLM agent prompts
│
├── 🐳 DEPLOYMENT & INFRASTRUCTURE
│   ├── Dockerfile                   # Container definition
│   ├── docker-compose.yml           # Production compose
│   ├── docker-compose.local.yml     # Local dev compose
│   ├── docker-compose.staging.yml   # Staging compose
│   ├── docker-compose.host.yml      # Host configuration
│   ├── .env.example                 # Environment template
│   ├── .env.local.example           # Local env template
│   ├── .env.staging.example         # Staging env template
│   ├── pyproject.toml               # Python project config
│   ├── lighthouse-budget.json        # Performance budgets
│   └── lighthouserc.json            # Lighthouse config
│
├── 🔗 VCS & IGNORE
│   ├── .gitignore                   # Git ignore rules
│   ├── .github/                     # GitHub workflows (CI/CD)
│   └── .mypy_cache/                 # Type checker cache (ignored)
│
└── 📦 APPLICATION DIRECTORIES
    ├── apps/                        # Django applications (12 modules)
    ├── automation/                  # Crawler & automation
    ├── config/                      # Django settings
    ├── templates/                   # HTML templates
    ├── static/                      # CSS, JS, fonts
    ├── media/                       # User uploads
    ├── ops/                         # Operations configs
    ├── nginx/                       # Nginx configs
    ├── tests/                       # Test suite
    ├── docs/                        # ⭐ DOCUMENTATION (organized)
    ├── assets/                      # ⭐ ASSETS (new)
    ├── data/                        # Data files
    ├── requirements/                # Python dependencies
    └── .venv/                       # Virtual environment
```

---

## 📚 DOCS Directory (Organized)

```
docs/
│
├── 📖 INDEX.md                          # ⭐ Start here - Documentation index
│
├── 📊 ANALYSIS (Gap & Strategy)
│   ├── IMPLEMENTATION_GAP_ANALYSIS.md   ← What's missing & priorities
│   └── ANALIZ_OZETI_RAPORU.md          ← Executive summary (Turkish)
│
├── 🗓️ ROADMAP (Planning & Timeline)
│   ├── DEVELOPMENT_ROADMAP_2026_2027.md ← 18-month detailed roadmap
│   └── MIMART_ANALIZ_OZETI.md          ← Technical architecture (Turkish)
│
├── 🔧 GUIDES (Operations)
│   ├── QUICK_REFERENCE_GUIDE.md         ← One-page quick start
│   ├── SERVER_SETUP_GUIDE.md            ← Infrastructure & monitoring
│   └── DEPLOYMENT_AND_OPERATIONS.md     ← Deployment & incident response
│
├── 🎨 DIAGRAMS (Visual)
│   ├── ARCHITECTURE_DIAGRAM.html        ← Interactive browser diagrams
│   └── HIBEROTA_ARCHITECTURE_REPORT.pdf ← Professional PDF report
│
├── 🏗️ ADR (Architecture Decisions)
│   └── ADR-001-technical-stack.md       ← Technical stack decisions
│
└── 📝 ORIGINAL DOCS (Faz 0-11)
    ├── 00_PROJECT_MASTER_PLAN.md        # Project overview
    ├── 01_ARCHITECTURE.md               # System architecture (TR)
    ├── 02_DATA_MODEL.md                 # Database design (TR)
    ├── 03_AUTOMATION.md                 # Crawler pipeline (TR)
    ├── 04_SECURITY.md                   # Security spec
    ├── 05_SEO_ANALYTICS_ADS.md          # Marketing setup
    ├── 06_UX_UI_FUNCTIONAL_SPEC.md      # UI specifications
    ├── 07_DEPLOYMENT_RUNBOOK.md         # Deployment procedures
    ├── 08_TEST_ACCEPTANCE.md            # Testing guide
    ├── 09_CODEX_CONTEXT_MAP.md          # Project context
    ├── 10_DECISIONS_AND_CHANGELOG.md    # Changelog
    └── [Other docs...]
```

---

## 💾 ASSETS Directory (New - Organized)

```
assets/
│
├── 🖼️ IMAGES (Logos & UI)
│   ├── logo.png                     # Main project logo
│   └── veorlogo.png                 # Veor collection logo
│
├── 📦 MEDIA (Design Files)
│   └── hiberota ux:uı.zip           # UX/UI design files
│
└── 📄 DOCS (Reference)
    ├── hiberotamarkakiti.pdf        # Brand guidelines (Turkish)
    └── HibeRota_Global_Call_Portals_2026.xlsx # Call portals reference
```

---

## 🔍 APPS Directory (12 Django Modules)

```
apps/
├── core/                            # Base setup, health checks
├── calls/                           # Grant calls (main entity)
├── sources/                         # Grant sources
├── institutions/                    # Organizations
├── ingestion/                       # Data ingestion pipeline
├── taxonomy/                        # Classifications
├── blog/                            # Blog & content
├── newsletter/                      # Email subscriptions
├── contact/                         # Contact forms
├── survey/                          # Grant survey & matching
├── analytics/                       # GA4, AdSense, SEO
└── security/                        # 2FA, audit logs
```

---

## 🤖 AUTOMATION Directory (Crawler)

```
automation/
├── adapters/                        # Source adapters
├── parsers/                         # Field extractors
├── pipeline/                        # Processing stages
├── http/                            # Safe HTTP client
└── tasks/                           # Celery tasks
```

---

## ⚙️ CONFIG Directory (Settings)

```
config/
├── settings/
│   ├── base.py                      # Shared settings
│   ├── local.py                     # Local dev settings
│   ├── test.py                      # Test settings
│   ├── staging.py                   # Staging settings
│   └── production.py                # Production settings
├── urls.py                          # URL routing
├── celery.py                        # Celery configuration
├── wsgi.py                          # WSGI server
└── asgi.py                          # ASGI server
```

---

## 📊 COMPARISON: Before vs After

### BEFORE (Messy)
```
hiberota_codex_project_pack/
├── .DS_Store                                    ❌ macOS junk
├── IMPLEMENTATION_GAP_ANALYSIS.md              ❌ Root cluttered
├── DEPLOYMENT_AND_OPERATIONS.md                ❌
├── DEVELOPMENT_ROADMAP_2026_2027.md            ❌
├── QUICK_REFERENCE_GUIDE.md                    ❌
├── ARCHITECTURE_DIAGRAM.html                   ❌
├── HIBEROTA_ARCHITECTURE_REPORT.pdf            ❌
├── ANALIZ_OZETI_RAPORU.md                      ❌
├── MIMART_ANALIZ_OZETI.md                      ❌
├── SERVER_SETUP_GUIDE.md                       ❌
├── logo.png                                    ❌ Mixed with docs
├── hiberota ux:uı.zip                          ❌
├── [30+ files cluttering root]                 ❌
└── apps/, docs/, ...                           ✅ OK
```

### AFTER (Organized) ✅
```
hiberota_codex_project_pack/
├── TASKS.md                                    ✅ Essential only
├── README.md                                   ✅
├── AGENTS.md                                   ✅
├── manage.py, pyproject.toml                   ✅
├── docker-compose.yml, Dockerfile              ✅
├── .gitignore, .github/                        ✅
│
├── docs/                                       ✅ ALL DOCUMENTATION
│   ├── INDEX.md (start here!)
│   ├── guides/ (deployment, operations)
│   ├── analysis/ (gap analysis)
│   ├── roadmap/ (18-month plan)
│   ├── diagrams/ (visual architecture)
│   └── adr/ (architecture decisions)
│
├── assets/                                     ✅ ALL ASSETS
│   ├── images/ (logos)
│   ├── media/ (design files)
│   └── docs/ (reference files)
│
├── apps/, automation/, config/                 ✅ Code
└── tests/, static/, templates/                 ✅ Code

Result: Clean root + organized docs + easy navigation 🎉
```

---

## 📈 Directory Statistics

| Directory | Files | Purpose |
|-----------|-------|---------|
| Root | 12 | Essential project files |
| docs/ | 25+ | All documentation |
| docs/guides/ | 3 | Operational guides |
| docs/analysis/ | 2 | Gap analysis & summary |
| docs/roadmap/ | 2 | Development roadmap |
| docs/diagrams/ | 2 | Architecture diagrams |
| assets/ | 6 | Images, media, references |
| apps/ | 12 | Django applications |
| automation/ | 5 | Crawler modules |
| tests/ | 350+ | Test suite |

---

## 🎯 Navigation Guide

### Quick Access (Root Level)
- **What to build?** → `TASKS.md`
- **How to start?** → `README.md`
- **LLM prompts?** → `AGENTS.md`
- **Documentation?** → `docs/INDEX.md` ⭐

### Documentation (docs/)
- **New team member?** → `docs/guides/QUICK_REFERENCE_GUIDE.md`
- **Missing features?** → `docs/analysis/IMPLEMENTATION_GAP_ANALYSIS.md`
- **18-month plan?** → `docs/roadmap/DEVELOPMENT_ROADMAP_2026_2027.md`
- **How to deploy?** → `docs/guides/DEPLOYMENT_AND_OPERATIONS.md`
- **Server setup?** → `docs/guides/SERVER_SETUP_GUIDE.md`
- **Visual overview?** → `docs/diagrams/ARCHITECTURE_DIAGRAM.html`

### Code (Apps)
- **Django apps** → `apps/`
- **Automation/Crawler** → `automation/`
- **Settings** → `config/`
- **Tests** → `tests/`

### Assets
- **Logos** → `assets/images/`
- **Design files** → `assets/media/`
- **References** → `assets/docs/`

---

## ✅ Cleanup Completed

### Removed ✅
- [x] `.DS_Store` (macOS junk file)
- [x] Cluttered root (moved 9 docs to docs/)
- [x] Mixed media files (moved to assets/)

### Organized ✅
- [x] Documentation → `docs/` with subfolders
- [x] Assets → `assets/` with subfolders
- [x] Root → Only essential 12 files

### Created ✅
- [x] `docs/INDEX.md` (documentation index)
- [x] `docs/guides/` (operation guides)
- [x] `docs/analysis/` (gap analysis)
- [x] `docs/roadmap/` (roadmap documents)
- [x] `docs/diagrams/` (visual documentation)
- [x] `assets/images/` (logos)
- [x] `assets/media/` (design files)
- [x] `assets/docs/` (references)

---

## 🚀 Benefits of New Structure

| Benefit | Impact |
|---------|--------|
| **Clean Root** | Easier to navigate, find essentials |
| **Organized Docs** | Quick access to any information |
| **Asset Separation** | Clear distinction between code & media |
| **INDEX.md** | Single entry point for documentation |
| **Scalable** | Easy to add new phases, documents |
| **Professional** | Looks polished & organized |

---

## 🔄 How to Maintain This Structure

### Adding New Documentation
1. Identify type: analysis, guide, roadmap, diagram?
2. Create in appropriate subfolder:
   - Analysis → `docs/analysis/`
   - Guides → `docs/guides/`
   - Roadmap → `docs/roadmap/`
   - Diagrams → `docs/diagrams/`
3. Link from `docs/INDEX.md`

### Adding New Assets
1. Identify type: image, media, reference?
2. Create in appropriate subfolder:
   - Images → `assets/images/`
   - Media → `assets/media/`
   - References → `assets/docs/`
3. Update this document

### Regular Cleanup
- **Monthly:** Remove old .DS_Store files
- **Quarterly:** Archive old docs to `docs/archive/`
- **Yearly:** Review and reorganize structure

---

## 📋 Files Overview

### Root Level (12 Essential Files)

| File | Purpose | Size |
|------|---------|------|
| `manage.py` | Django CLI | 1 KB |
| `README.md` | Quick start | 2 KB |
| `TASKS.md` | Task checklist | 24 KB ⭐ |
| `AGENTS.md` | LLM prompts | 8 KB |
| `pyproject.toml` | Project config | 1 KB |
| `Dockerfile` | Container image | 1 KB |
| `docker-compose.yml` | Compose config | 3 KB |
| `.gitignore` | Git ignore rules | 1 KB |
| `lighthouse-budget.json` | Performance budget | 1 KB |
| `lighthouserc.json` | Lighthouse config | 1 KB |
| `.env.example` | Env template | 2 KB |
| `.github/` | CI/CD workflows | - |

### Documentation (25+ Files)

- `docs/INDEX.md` ⭐ Start here
- `docs/guides/` - 3 operational guides
- `docs/analysis/` - 2 analysis documents
- `docs/roadmap/` - 2 roadmap documents
- `docs/diagrams/` - 2 visual diagrams
- `docs/adr/` - Architecture decisions
- `docs/00-10/*.md` - Original documentation

### Assets (6 Files)

- `assets/images/` - 2 logos
- `assets/media/` - 1 UX/UI file
- `assets/docs/` - 2 references

---

## 🎉 SUMMARY

**Status:** ✅ **PROJECT STRUCTURE ORGANIZED**

### What Changed
- ✅ Moved 9 documentation files to `docs/`
- ✅ Moved 6 asset files to `assets/`
- ✅ Removed `.DS_Store` junk
- ✅ Created `docs/INDEX.md` (navigation hub)
- ✅ Organized into logical subfolders

### Result
- ✅ Clean root directory
- ✅ Easy navigation
- ✅ Professional appearance
- ✅ Scalable structure
- ✅ Better onboarding for new team members

### Next Steps
- Read `docs/INDEX.md` for documentation
- Use `TASKS.md` for project tasks
- Follow `README.md` for setup
- Reference `docs/guides/` for operations

---

**Organized By:** AI Architecture System  
**Date:** 30 Haziran 2026  
**Status:** ✅ COMPLETE
