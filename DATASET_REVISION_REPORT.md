# Dataset revision report

Original archive: `../Timble_/datasets/datasets.zip`. SHA-256: `dd7d140d517d5941784816736fb2ea50650141ac12fc84f6b9e039b5a15a0ced`.
All ten archive CSVs were extracted into `.work/legacy_archive`, parsed, and inventoried. No spreadsheets or historical enrollment files are present in this archive. Other loose legacy rosters are not silently merged: annual counting and identity de-duplication would require a separately validated mapping.

## Per-file and per-column classification

| Original | New | KEEP | TRANSFORM / DERIVE | REMOVE |
|---|---|---|---|---|
| Programs | programs.csv | program_code, program_name, max_year_level | is_active=true: administrative import status | program_id |
| subjects | subjects.csv and review | subject_name, is_active | canonical code from curriculum; lexicographic choice among same-identity aliases; conflicting identities held | subject_id, subject_description |
| Curriculum | review/current candidates | program_code | latest by effective_start per program | curriculum_id, effective_end, program_id after flattening |
| curriculum_subject | review/program_subject_candidates.csv | subject_code, units | year_level_id to integer; status to is_active; requirement_type to elective candidate | source IDs, old term IDs, subject type, elective_group_id; names are retained in review only |
| Faculty | faculty.csv | names, max_teaching_load | LEGACY-F-{id} import key; normalized faculty_type; status to boolean | faculty_id, availability_status |
| FacultyExpertise | review/unresolved.json | full original row for review only | no automatic permission mapping | expertise/name redundancy from runtime |
| Room | rooms.csv | capacity | room_name to room_code; lec to LECTURE and lab to LAB per user clarification; status boolean | none silently discarded |
| year_level | integer fields | order values for cross-checking | IDs 1â€“4 equal documented year order | master table, status and label |
| semester | none | none | none | all columns |
| Timeslot | none | none | none | all columns |

## Counts and validation scope

- programs.csv: 6 accepted rows.
- subjects.csv: 121 accepted rows.
- program_subjects.csv: 0 accepted rows.
- program_subject_prerequisites.csv: 0 accepted rows.
- block_sections.csv: 0 accepted rows.
- faculty.csv: 18 accepted rows.
- faculty_teaching_rules.csv: 0 accepted rows.
- rooms.csv: 12 accepted rows.
- subject_aliases.csv: 40 accepted rows.
- historical_enrollment.csv: 0 accepted rows.

546 unresolved source rows are retained with reasons in `review/unresolved.json`. 361 current curriculum candidates were flattened; 247 prerequisite expressions require mapping. Header-only outputs are deliberate, not evidence of completed academic data.

## Assumptions and missing information
- Program active status is an administrative default because the source has no status.
- LEGACY-F identifiers preserve source identity and are not institutional employee numbers.
- User clarification authorizes two room categories: LAB and LECTURE; all source rooms map directly.
- User clarification: no subject failure-rate master field. Failure probability is entered at forecast generation; only calculation evidence retains the assumption used.
- lec_hours/lab_hours cannot establish duration per meeting and weekly meeting count; candidates retain their original values in the review JSON.
- Latest curriculum is selected by numeric effective_start. Duplicate program/subject candidates remain in review rather than being arbitrarily merged.
- No block sections or historical enrollments were present in the archive. Those outputs contain headers only. Subject aliases derive from alternate curriculum codes for the same legacy subject identity.
- Textual prerequisites are preserved for manual mapping, not interpreted as arbitrary AND/OR rules.
- Explicit teaching permission must be confirmed for all expertise records.

## Reproduce
`python scripts/revise_datasets.py`, then `python backend/manage.py validate_datasets`. The validator uses the same transactional importer as the UI and rolls all changes back. The separate `datasets/demo` package contains synthetic, labeled defense examples and is never included in datasets.zip.

The revised archive contains only the ten new schema CSVs. The legacy archive is read-only and its hash is rechecked after transformation.

Every original column is separately classified in `datasets/review/column_classification.csv`. KEEP in review is not a claim that a field was accepted into runtime data.

## Single-package import
Upload `datasets.zip` through Bulk Management → Dataset ZIP (all files). The application validates the ten files in dependency order and commits them atomically. The archive contains the verified subset; header-only outputs still represent unresolved or absent source data. `demo-datasets.zip` is a separate synthetic package and is not mixed into the revised real datasets.
