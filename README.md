# Timble V2

A clean Django/React academic planning system. Historical enrollment → forecasting → course offerings → runtime scheduling scenario → Pyomo model → HiGHS → explainable timetable.

## Verified implementation

- Master-data CRUD, session authentication and CSRF protection.
- Ten CSV formats with templates, transactional preview/commit, relationship validation, row errors and insert/update/skip counts.
- Prior-year prerequisite forecasting, MAX within a program, SUM reporting across programs, calculation evidence and idempotent finalization.
- Pyomo binary scheduling with HiGHS, faculty/room/block collision prevention, categorical teaching rules, capacity/type checks, consecutive periods, weekly load and distinct meeting days.
- Background solver process, saved input snapshots, final assignments, seven matrix views, assignment explanations and real terminal solver measurements.
- Separate synthetic demonstration package and reproducible real-data conversion.

**User clarifications:** failure probability is entered when generating a forecast, not stored as a Subject attribute. The applied assumption is retained in each calculation's evidence. Rooms are `LAB` or `LECTURE`.

## Start on Windows

Python 3.13 and Node 24 were used for verification. Run from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
npm.cmd --prefix frontend ci
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py createsuperuser
```

The local `.env` already points to the verified-empty MySQL `timble` database, now initialized with fresh V2 migrations. Credentials are excluded from version control. No legacy rows were imported. For another machine, copy `.env.example` to `.env` and set the connection values. Omitting database variables selects SQLite. `SQLITE_PATH` explicitly overrides MySQL/PostgreSQL and is used by isolated tests. Environment values override `.env`.

In separate terminals:

```powershell
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
npm.cmd --prefix frontend run dev
```

Open http://127.0.0.1:5173 and sign in with the account you created. `npm.cmd` avoids PowerShell execution-policy problems with `npm.ps1`. No default password or inherited legacy account is created.

## Demonstration

```powershell
.\.venv\Scripts\python.exe backend\manage.py load_demo
```

This explicit command imports synthetic `DEMO-` records. In Forecasting, select **DEMO-CS**, academic year **2026-2027**, capacity **30**, and failure assumption **0.05**. Generate and inspect the calculation, then finalize. In Scheduling studio, choose the finalized forecast and generate a schedule. Explore Timetable, Solver progress, and Optimization computation.

The verified example has 100 source students; prerequisite adjustment produces 95 students and four sections. Twelve component offerings are scheduled. Room waste is 70, best bound 70, gap 0, and independently reconstructed conflicts are zero. Runtime is machine-dependent. Actual browser-test evidence is in `artifacts/verified-demo-run.json`; screenshots are in `artifacts/`.

## Import all datasets from one ZIP

Open **Bulk management → Dataset ZIP (all files)**. Select `datasets/datasets.zip`, click **Validate package**, review the per-file counts and errors, then click **Import all datasets**. Every file is processed in dependency order inside one transaction: any failed row rolls back the entire package, including updates to existing records.

The UI also provides **Download ZIP templates**, **Download revised datasets**, and **Download demo ZIP**. The separate `datasets/demo-datasets.zip` contains the full synthetic example. No extraction or one-by-one upload is needed. The ZIP must contain the ten canonical CSV filenames at its root; keep header-only CSVs for datasets with no records. Aliases are processed before curriculum and history. Single CSV import remains available.

ZIP limits are 10 MB uploaded, 10 MB per expanded CSV, and 40 MB expanded total. Duplicate, missing, nested/unexpected, encrypted and damaged entries are rejected. The import reads archive members without extracting files to disk. Validation does not retain records; commit repeats validation.

## Real datasets and unresolved source information

`datasets/datasets.zip` contains only the ten revised CSV files. Accepted rows: 6 programs, 121 subjects, 18 faculty, 12 rooms and 40 aliases. The archive contains no historical enrollment or block-section records. **361 current curriculum candidates and 247 prerequisite expressions are preserved for review**, not silently replaced with invented meeting patterns. There are 546 unresolved source rows in total, including ambiguous subject identities and faculty expertise without explicit teaching permissions.

`datasets/review/program_subject_candidates.csv` has the new curriculum headers. Fill verified durations, weekly meeting counts and room requirements, resolve duplicate identities, then validate/import through Bulk Management. Missing meeting-pattern policy remains an institutional-data blocker, not a missing import feature. Do not use the header-only source curriculum file as evidence that real curriculum import is complete.

```powershell
.\.venv\Scripts\python.exe scripts\revise_datasets.py
.\.venv\Scripts\python.exe backend\manage.py validate_datasets
```

The first command reads the legacy archive without changing it. The second uses the production CSV importer and rolls back all data mutations. Read [DATASET_REVISION_REPORT.md](DATASET_REVISION_REPORT.md) for every mapping, assumption and unresolved category.

## Verification

```powershell
.\.venv\Scripts\python.exe scripts\verify.py
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts\verify_database.py
.\.venv\Scripts\python.exe scripts\browser_smoke.py
```

- `verify.py`: 51 backend tests on isolated SQLite, Django checks and migration-drift check.
- Frontend: five unit/UI tests and production build.
- `verify_database.py`: real MySQL import → forecast → finalize → solve → persist inside a transaction, then full rollback. No demo records remain.
- `browser_smoke.py`: disposable SQLite database, local ports 8000/5173, Microsoft Edge in headless mode, full UI workflow and 390-pixel mobile-width check. Ports must be free. It stops its servers on completion.
- A full MySQL test-suite attempt could not create a test database because `timble_user` lacks that privilege. `verify_mysql.py` is available when an administrator provides a test account with create/drop privileges; it always chooses a unique test-schema name. Privileges were not changed.

## Architecture and operating policies

Backend business logic is under `apps/forecasting/services` and `apps/scheduling/services`; solver code is confined to `apps/scheduling/optimization`. Runtime scenario and independent validation live in `apps/scheduling/domain`. Frontend modules are grouped by feature. See [MANUSCRIPT_REVISION.md](MANUSCRIPT_REVISION.md) and [docs/DATABASE.md](docs/DATABASE.md).

Missing teaching rules mean ineligible. Each offering keeps one faculty across all meetings. Weekly load is occupied one-hour periods. Meetings of the same offering use distinct days. Monday–Saturday have twelve periods, 07:30–19:30. Sections remain program-specific; shared-subject totals are reported, not pooled into cross-program offerings. Active blocks are initially associated in section-code order; users can review/edit offering-block links before scheduling.

The solver records one real terminal metric sample, not a fabricated progress series. A feasible time-limited result is distinguished from a proven optimum. The 60-second limit covers solver execution, not model construction. Equal-cost timetables may differ. Large institutional instances need scale evaluation; the verified demonstration is not a throughput benchmark.

## Deployment boundary

This delivery is local, not publicly deployed. Set a strong secret, `DJANGO_DEBUG=0`, allowed hosts, trusted HTTPS origins, an HTTPS reverse proxy and a production Django server for deployment. The current background subprocess worker is suitable for local operation; a managed task queue, cancellation and crash recovery are not implemented. A worker interrupted by process termination can leave a RUNNING record; inspect before regenerating. All authenticated users currently have the same application permissions.

No obsolete database compatibility models or learning-agent dependencies are present. The legacy project remains unchanged.
