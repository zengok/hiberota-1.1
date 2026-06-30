# First 72 Hour Production Monitoring Report

Snapshot time: 2026-06-29T21:02:42Z

## Summary

Production is healthy at this checkpoint. Public endpoints respond with HTTP 200, all core containers are running, Redis queue depth is 0, review queue is empty, and call data quality verification passes.

The production scheduler is open only for the reviewed allowlist `src-0011,src-0017` with `SOURCE_SCHEDULER_MAX_DUE_SOURCES=1`. The first beat cycle ran `sources.schedule_due_sources` and returned `0` because allowlisted sources were not due yet. No broad crawl was dispatched.

## Site Health

| Check | Result |
|---|---:|
| `/health/live` | 200, 0.036s |
| `/health/ready` | 200, 0.137s |
| `/` | 200, 0.198s |
| `/cagrilar/` | 200, 0.279s |
| Docker services | web, worker, beat, postgres, redis healthy; nginx up |
| Disk `/` | 13% used |
| Redis queue `celery` | 0 |

## Crawl and Source Health

| Metric | Value |
|---|---:|
| Sources total | 249 |
| Active sources | 246 |
| Paused sources | 3 |
| Degraded/blocked/manual-only sources | 0 |
| Average source health score | 100.0 |
| Sources with consecutive failures | 2 |
| Crawl runs completed | 22 |
| Crawl runs failed | 2 |
| Open review items | 0 |

Known failed crawl runs are old controlled-run evidence:

| Run | Source | Error |
|---:|---|---|
| 1 | `src-0001` | HTTP 403 |
| 2 | `src-0002` | HTTP 404 |

These sources are not in the production scheduler allowlist.

## Public Call Quality

| Workflow status | Count |
|---|---:|
| Published | 3 |
| Rejected | 16 |
| Review | 0 |

| Availability status | Count |
|---|---:|
| Open | 1 |
| Closed | 4 |
| Unknown | 14 |

`verify_call_data_quality --require-checked --fail-on-issues` result:

- Checked calls: 19
- Duplicate candidates: 0
- Availability mismatches: 0
- Result: pass

## Source Decision Snapshot

| Source | Last run | Published | Rejected | Review | False-positive rate |
|---|---|---:|---:|---:|---:|
| `src-0011` | completed | 1 | 0 | 0 | 0.0% |
| `src-0014` | completed | 1 | 7 | 0 | 25.0% |
| `src-0017` | completed | 1 | 3 | 0 | 75.0% |
| `src-0018` | completed | 0 | 0 | 0 | 0.0% |
| `src-0023` | completed | 0 | 0 | 0 | 0.0% |

## Current Watch Items

- Keep scheduler allowlist limited to `src-0011,src-0017` until both complete a due crawl cycle without new false positives.
- Do not add `src-0014` to the scheduler allowlist yet; it is useful but has a high rejected/general-page history.
- Investigate `src-0001` and `src-0002` separately before any retry because one returned 403 and the other 404.
- Backup directory evidence was not found in the checked default paths during this snapshot; keep backup verification as an operations follow-up rather than assuming it is covered by this report.

## Rollback

If scheduler behavior becomes noisy, set:

```env
SOURCE_SCHEDULER_ROLLBACK_PAUSED=true
```

Then recreate `web`, `celery_worker`, and `celery_beat` containers so the runtime env is reloaded.
