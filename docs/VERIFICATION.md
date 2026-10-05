# Verification record

Verified on 2026-10-06 (Asia/Singapore).

| Check | Result |
|---|---|
| Fresh migrations | Applied to SQLite and the verified-empty MySQL timble database |
| Backend suite | 51 passed on isolated SQLite |
| Frontend tests | 5 passed |
| Production frontend build | Passed |
| Django system checks | Passed |
| Migration drift | No changes detected |
| Static analysis | Ruff passed |
| Real source CSV package | Production validators passed; all validation writes rolled back |
| Synthetic CSV package | Production validators passed; all validation writes rolled back |
| Actual MySQL workflow | Ten-file ZIP import, OPTIMAL, 12 persisted assignments, objective=bound=70, gap=0, 1 node; all data rolled back |
| Browser workflow | Edge headless: login, ten-file ZIP preview/commit, CRUD, forecast, finalization, background solve, timetable, explanation, matrices, collision demo, solver metrics |
| Mobile | 390×844 viewport, no horizontal document overflow |
| Browser errors | None |
| Legacy archive | SHA-256 unchanged by transformation |

Full MySQL unit-test database creation was denied by the database account (1044). No permission changes were made. The transaction-based MySQL workflow verified the actual deployed engine without creating another schema.

The actual measurements are in `artifacts/verified-demo-run.json` and `artifacts/database-verification.json`. These contain synthetic academic records only. Runtime is an observation, not a performance guarantee.

## Outstanding institutional data

The real archive has no block sections or historical enrollment. Meeting-pattern conversion and prerequisite interpretation require confirmation. Faculty expertise does not establish explicit permissions. Ambiguous subject identities remain in the audit package. The application is executable and verified; full institutional data readiness is not claimed.

ZIP regression cases include cross-file dependency resolution, aliases before curriculum, preview rollback, commit idempotence, late-file rollback of inserts and updates, missing/duplicate/unexpected entries, size limits, invalid UTF-8, authenticated downloads and filename consistency.
