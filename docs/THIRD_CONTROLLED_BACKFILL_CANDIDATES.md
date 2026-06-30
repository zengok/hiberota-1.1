# Third Controlled Backfill Candidate List

Snapshot time: 2026-06-29T21:10:00Z

This list does not authorize a production crawl by itself. It ranks candidate sources for the next controlled backfill after parser fixture review. No crawl task was queued while preparing this document.

## Selection Rules

- Use only active, static HTML sources.
- Prefer priority 1 sources with clear public value and non-empty audience hints.
- Do not include sources with robots `restricted`.
- Do not retry sources with known 403/404 or timeout until separately reviewed.
- Require a sanitize fixture before any source whose listing structure is unknown or likely to produce programme/guidance false positives.

## Robots Dry Check

Command used:

```bash
python manage.py verify_source_robots \
  --source-key=src-0020 \
  --source-key=src-0022 \
  --source-key=src-0076 \
  --source-key=src-0085 \
  --source-key=src-0120 \
  --source-key=src-0242
```

Dry-run result:

| Source | Robots result | Note |
|---|---|---|
| `src-0020` | allowed | TUBITAK support portal |
| `src-0022` | restricted | Exclude from backfill candidate list |
| `src-0076` | allowed | ERC grant page |
| `src-0085` | allowed | Eureka open calls |
| `src-0120` | allowed | UKRI opportunity finder |
| `src-0242` | unknown | Timeout; exclude until retried outside backfill |

## Priority A — Fixture First, Then Small Backfill

| Source | Why | Risk | Required parser fixture work |
|---|---|---|---|
| `src-0085` Eureka Open Calls | Strong SME relevance and likely real call listing. | Medium: cards may include programme pages and archived calls. | Add sanitized listing fixture, detail-link keyword test, deadline/status extraction test. |
| `src-0120` UKRI Funding Finder | High-value research/SME source with frequent opportunities. | Medium: many opportunity types and filters; potential duplicate titles. | Add listing fixture with at least two opportunity cards, detail fixture with deadline/status and eligibility snippets. |

## Priority B — High Value, Higher Parser Risk

| Source | Why | Risk | Required parser fixture work |
|---|---|---|---|
| `src-0020` TUBITAK Destekler | Core Turkey research source. | High: Turkish portal pages may be support-programme pages rather than individual calls. | Add Turkish listing/detail fixture, Turkish deadline/status labels, programme-vs-call false-positive tests. |
| `src-0076` ERC Apply Grant | High-value researcher source. | High: current URL is a grant-scheme/programme page and may not expose individual open calls. | Confirm whether a lower-level calls page/feed exists; add false-positive fixture before any production crawl. |

## Excluded For Now

| Source | Reason |
|---|---|
| `src-0022` Ufuk Avrupa Çağrıları | Robots dry-check returned restricted/http_403. |
| `src-0242` Australian Research Council | Robots dry-check timed out. Retry robots only later; do not crawl yet. |
| `src-0014` IDRC Funding | Valuable, but prior backfills produced several rejected/general pages; keep out of scheduler until adapter is more source-specific. |
| `src-0015` Wellcome Funding | Prior run returned HTTP 202 and no calls; needs fetch behavior review before retry. |
| `src-0018` Grand Challenges and `src-0023` KOSGEB | Already used in second controlled batch and produced no calls with the current generic parser. |

## Fixture Review Status

Completed on 2026-06-30:

- `src-0085` Eureka Open Calls has sanitized listing/detail fixtures.
- `src-0120` UKRI Funding Finder has sanitized listing/detail fixtures.
- Static HTML discovery now accepts safe `www`/non-`www` host variants and filters common status/apply guide links.
- Static HTML parsing now extracts common `dt`/`dd` label-value status and deadline fields such as `Opportunity status` and `Closing date`.

No production crawl was queued while updating these fixtures.

## Dry Run Result

Production dry-run completed on 2026-06-30 without `--commit`:

```text
Planned sources: 2
1. src-0085 | active | src-0085_html_v1 | countdown=0s
2. src-0120 | active | src-0120_html_v1 | countdown=30s
Dry run complete. Run again with --commit to enqueue tasks.
```

Do not run the committed backfill until the parser fixture changes are deployed to the target environment.

## Limited Production Backfill Result

Completed on 2026-06-30 after parser deployment:

- `src-0120` queued successfully and persisted 5 review-stage records.
- `src-0085` first hit a safe HTTP `www` allowlist issue; the allowlist was fixed and the source then persisted 5 review-stage records.
- All 10 generated records were confirmed as false positives: UKRI guidance/filter pages and Eureka programme pages rather than individual open calls.
- The false positives were rejected with the reason `Controlled backfill false positive: guidance, listing filter, or programme page rather than an individual open call.`
- Final review queue: 0 open records.
- Final quality check: duplicate candidates 0, availability mismatches 0.

Decision: do not widen scheduler allowlist for `src-0085` or `src-0120` until a lower-level official opportunity feed, API, sitemap subset, or more precise detail-link selector is identified.

## Proposed Next Safe Step

Inspect `src-0120` and `src-0085` for an official lower-level opportunity feed/API or sitemap subset. Keep both sources out of the scheduler allowlist until that selector is proven with fixtures.
