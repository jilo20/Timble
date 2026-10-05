# Legacy audit — before implementation
Reference project: ../Timble_ (read only). No database or migrations are reused.

| Classification | Reference | Decision |
|---|---|---|
| REUSE | frontend/public/logo.svg; src/index.css brand colors | Preserve logo and green/brown palette. |
| REFACTOR | sidebar, tables, forms, import preview UX | Feature-based React components, accessible controls and revised navigation. |
| REFACTOR | offered_subject_service.py demand_of and shared aggregation | Preserve prerequisite failure adjustment, MAX within program, SUM across programs; remove obsolete configuration. |
| REFACTOR | historical_demand_service.py | Prior academic year, canonical subject relationships and alias resolution. Missing data is an error, never zero. |
| REFACTOR | section_materialization_service.py | Transactional, idempotent generation; retain program provenance. Shared-subject totals are reported across programs; sections remain program-specific because the revised offering has one program_subject FK. |
| REFACTOR | bulk import | Strict revised headers, atomic validation/commit, relationship validation and templates. |
| REFACTOR | authentication | Django sessions and CSRF, authenticated APIs; no inherited credentials. |
| REMOVE | old migrations and models | Fresh migrations only. |
| REMOVE | custom CSP, optimization agents, training and reward code | New Pyomo model solved by HiGHS. |
| REMOVE | curriculum version selection, semester, timeslot, expertise, availability | No runtime compatibility layers. |

## Explicit revised policies
One-hour periods, Monday–Saturday, 07:30–19:30. Missing teaching rule means ineligible (displayed as CANNOT). One faculty per offering across its meetings. Weekly teaching load is measured in occupied periods. Repeated meetings occur on distinct days. No-prerequisite subjects use their own previous-year enrollment without progression loss, matching the inspected legacy fallback. Prerequisite subjects use MAX of adjusted prerequisite enrollments. Decimal demand is rounded upward once, after MAX. Cross-program SUM is displayed; program-specific sections are not claimed to be pooled.

## Dataset integrity
The archive has ten CSV files, no historical enrollment or blocks. Its faculty expertise records have no explicit permission category; they must not be converted automatically. Failure rates and per-meeting patterns are absent. Retain unresolved rows for review rather than fabricate academic values. Derived LEGACY-F- identifiers are import keys, not claimed institutional employee numbers.

## User clarification, 2026-10-06
Failure rate is a runtime forecast assumption, not a Subject field. Persist the applied rate only in computation evidence. Room categories are LAB and LECTURE. This overrides the initial specification and enables direct room conversion.
