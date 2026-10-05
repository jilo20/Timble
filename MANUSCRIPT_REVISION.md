# Timble V2: Revised Technical Manuscript

Implementation-based revision, 6 October 2026. This document was written after application implementation, passing backend/frontend tests, a successful real-browser workflow, and a rollback-only workflow on MySQL. It describes the code that exists, including its limits. The revised real-data archive is valid for its accepted subset; unresolved institutional records are explicitly distinguished from the synthetic demonstration.

## A. Revised system overview

Timble V2 is an academic demand-planning and timetable-generation application. The implemented workflow is historical enrollment → forecasting → course offerings → scheduling scenario → Pyomo → HiGHS → final timetable. Master data provide the program, current curriculum, subject, faculty, teaching-rule, room and block identities used throughout the workflow. A forecast describes demand; an offering describes a teaching requirement; a schedule assignment records the actual resource and time decision. These are separate entities.

A user first validates academic records through CRUD forms or transactional CSV imports. The user then specifies the target academic year, program scope, section capacity and a forecast failure-probability assumption. Forecast results retain their computation evidence. Finalization materializes lecture and laboratory offerings and links them to real student blocks. A scheduling run saves a complete input snapshot before invoking optimization. Successful assignments are independently checked and persisted with solver measurements.

The application contains no reinforcement-learning subsystem. The scheduling problem is formulated explicitly as a binary mixed-integer linear optimization model. Feasibility is determined by hard constraints, while the objective selects a timetable with minimal unused room capacity per meeting.

## B. Implemented system architecture

| Layer | Actual implementation | Responsibility |
|---|---|---|
| Frontend | React/Vite under `frontend/src/features` | Master-data editing, imports, forecasts, timetable and mathematical demonstrations |
| Authentication | Django sessions; CSRF-protected session endpoint | Login, logout and authenticated application APIs |
| HTTP API | Django REST Framework views and generated resource viewsets | Validate requests and delegate operations |
| Master data | `apps/master_data/models` | Current academic entities, uniqueness and relationship validation |
| Bulk management | `apps/bulk_import/services/importer.py` | Exact headers, normalization, key resolution, preview, atomic commit |
| Forecasting | `apps/forecasting/services` | Prior-year evidence, adjustment, aggregation and offering materialization |
| Scheduling domain | `apps/scheduling/domain` | In-memory scenario, matrices, independent occupancy validation and explanations |
| Optimization | `apps/scheduling/optimization` | Sparse binary variables, constraints, objective and solver integration |
| Persistence | `apps/scheduling/services/schedule_service.py` | Background-worker lifecycle and transactional result storage |
| Database | Configured MySQL; SQLite for isolated tests; optional PostgreSQL configuration | Relational data and immutable calculation/run evidence |

A scheduling scenario is a dataclass, not a master table. Its serialized value is saved inside a ScheduleRun for reproducibility. Similarly, forecast computation evidence is a JSON value within ForecastResult, not a historical curriculum version. Pyomo imports are confined to the optimization package. The mathematical result validator does not import Pyomo and reconstructs the occupied periods independently.

The current background worker is a separate Python process launched by the API. An atomic status update claims one queued run. The frontend polls the run and displays its true state. This is not a distributed job queue; cancellation, worker supervision and automatic recovery after process termination are not implemented.

## C. Revised database design

The application contains 17 domain tables, described below and enumerated field-by-field in `docs/DATABASE.md`. Foreign keys preserve identity rather than duplicating academic names. Referenced academic records are generally protected from deletion; activity flags permit exclusion from future operations.

| Table | Purpose and important relationships | Why it exists |
|---|---|---|
| program | Unique code, name, maximum year, active flag | Defines a program and valid integer year range |
| subject | Unique code, name, active flag | Canonical subject identity, independent of program |
| program_subject | Program→Subject; integer year; units; component duration, frequency and room type | Current curriculum and teaching requirements |
| program_subject_prerequisite | ProgramSubject→ProgramSubject within the same program | Queryable prerequisite graph; self/cyclic links rejected |
| block_section | Program, integer year, section code, count and active flag | Student groups protected against simultaneous meetings |
| faculty | Employee code, names, type, maximum weekly teaching load and activity | Minimal instructor resource |
| faculty_teaching_rule | Faculty→Subject; unique pair; categorical rule | Explicit eligibility and mandatory assignment requirements |
| room | Unique code, LAB/LECTURE, capacity and activity | Physical teaching resources |
| subject_alias | Unique normalized alias→Subject | Resolves inconsistent historical/import codes |
| historical_enrollment | Academic year, Program, Subject, enrollment count; unique triple | Normalized observed demand |
| forecast_run | Target year, status, capacity, generating/finalizing users and times | Forecast lifecycle and attribution |
| forecast_result | Run→ProgramSubject; source, adjustment, demand, sections, method and evidence | Persisted forecast output with its calculation inputs |
| course_offering | Result→ProgramSubject; section, expected students, component, duration and meetings | Teaching requirements, without assigned timetable fields |
| course_offering_block | Offering→Block; unique pair | Many-to-many attendance relationship |
| schedule_run | Year, solver, status, objective/bound/gap/nodes, times, snapshot and diagnostic | A reproducible optimization execution |
| schedule_assignment | Run→Offering/Faculty/Room; meeting, day, start and duration | Final timetable decisions |
| solver_metric | Run, sequence, elapsed time and native solver measurements | One genuine terminal observation per completed solve |

Django additionally maintains authentication, permission, session, content-type and migration bookkeeping tables. Their names and roles are listed in the database appendix. They are framework infrastructure rather than academic master entities.

The previous Semester, YearLevel, Timeslot, FacultyExpertise, FacultyAvailability, cohort curriculum selection and learning-related tables are absent. Integer year levels are validated against the program maximum. Time is generated from day/period configuration. Explicit categorical teaching rules replace ambiguous expertise/preference semantics. Only the current curriculum is represented.

Per the user's implementation clarification, **Subject has no failing_rate column**. The forecasting request supplies a probability; calculation evidence preserves the assumption actually used, so an old result remains explainable. Room types are exactly LAB and LECTURE.

## D. Current curriculum structure

The implemented relationship is Program → ProgramSubject → Subject. The pair (program, subject) is unique. A ProgramSubject carries an integer year level, units, lecture/lab duration in one-hour periods, weekly meeting counts, room requirements and elective/activity flags. Zero duration and zero frequency must occur together for an absent component. At least one component must be present. Year zero is invalid.

Prerequisites reference other ProgramSubject records in the same program. Validation traverses the prerequisite graph before saving a link and rejects cycles. The application does not select historical curriculum versions, interpret free-text prerequisites during forecasting, or infer elective demand from a chairman's estimate. The dataset audit retains unresolved textual prerequisites until their relationships are confirmed.

## E. Implemented forecasting methodology

The evidence source for target academic year \(y\) is exactly the previous academic year \(y-1\). Academic years must use consecutive YYYY-YYYY values. Missing history is an error and rolls back the entire forecast transaction; it is never interpreted as zero enrollment. An explicitly recorded zero is valid evidence.

Let \(H_{g,q,y-1}\) denote historical enrollment in program \(g\), prerequisite subject \(q\), in the prior year. Let \(\rho\in[0,1]\) be the failure assumption entered for this run, and let \(Q_{g,s}\) be the direct prerequisites of target subject \(s\). The current implementation uses one user-entered probability for the forecast request; it does not estimate individual probabilities from observed outcomes.

For a target with prerequisites:

\[
A_{g,q}=H_{g,q,y-1}(1-\rho),\qquad
N_{g,s}=\left\lceil\max_{q\in Q_{g,s}} A_{g,q}\right\rceil.
\]

Decimal arithmetic is used before a single upward rounding after MAX. This retains the inspected legacy program-level MAX behavior; it does not claim to calculate the intersection of individual students who passed every prerequisite. Without student-level histories, such an intersection cannot be established.

For a target with no prerequisites:

\[
N_{g,s}=H_{g,s,y-1}.
\]

This own-prior-enrollment fallback matches the relevant legacy behavior. It does not apply the prerequisite progression-loss assumption. The method is recorded as OWN_PRIOR_ENROLLMENT, while prerequisite results use PREREQUISITE_MAX.

For positive section capacity \(C\):

\[
K_{g,s}=\left\lceil N_{g,s}/C\right\rceil.
\]

For a subject shared by programs, the API reports:

\[
N_s^{\text{reported}}=\sum_g N_{g,s}.
\]

The SUM is a cross-program demand summary. **The implemented offering generator creates program-specific sections; it does not pool these totals into a shared cross-program section.** This maintains the revised single ProgramSubject foreign key and explicit provenance. All formulas here describe the implemented behavior, not a hypothetical pooled-section algorithm.

The selected MAX source determines source_enrollment and failure_adjustment. Evidence retains every source considered, its history ID, adjusted value, rate, chosen source, rounding, capacity and component configuration. This is especially important where several prerequisites have different counts. Master-data changes after generation do not change the saved computation or captured component requirements.

## F. Verified forecast worked example

The synthetic DEMO-CS dataset contains Programming Foundations with a prior-year enrollment of 100 and Algorithms with Foundations as its prerequisite. The user selects \(\rho=0.05\), academic year 2026-2027 and capacity 30. These are labeled demonstration assumptions, not measurements from the institution.

\[
\text{failure adjustment}=100(0.05)=5,
\qquad A=100-5=95,
\qquad K=\lceil95/30\rceil=4.
\]

Algorithms produces sections of 30, 30, 30 and 5 expected students. Each has a two-period lecture meeting and a three-period lab meeting, producing eight component offerings. Foundations has no prerequisite, so its own 100-student history produces four lecture offerings with counts 30, 30, 30 and 10. The total is twelve offerings, each requiring one meeting in this dataset.

The finalization service locks the forecast run, requires sufficient active blocks, and creates offerings and block links within one transaction. Repeated finalization returns the already-finalized run without duplicate offerings. Initial block associations follow section-code order. Users can inspect and edit the attendance links, including linking an offering to several blocks, before scheduling.


## G. Mathematical scheduling formulation

Timetabling is a constraint optimization problem because the decision must satisfy several simultaneous resource and attendance restrictions while minimizing an explicitly stated cost. Binary variables represent discrete alternatives. The current model is linear: all constraints and the objective are sums of binary variables multiplied by constant data.

`optimization/variables.py` creates the following Pyomo RangeSet objects:

\[
O=\{1,\ldots,n\},\quad F=\{1,\ldots,m\},\quad
R=\{1,\ldots,k\},\quad B=\{1,\ldots,b\},\quad
D=\{1,\ldots,d\},\quad P=\{1,\ldots,p\}.
\]

These denote offerings, active faculty, active rooms, participating active blocks, configured days and daily periods. For offering \(o\), meeting indices range from 1 to its required meeting count \(M_o\). This range is generated per offering rather than stored as a separate master table.

Database IDs are explicitly mapped to contiguous mathematical indices. Consequently, a database primary key need not equal the displayed O, F, R or B index. The snapshot retains both the original ID and the 1-based index. Programming-list positions are internal implementation details and are never presented as zero-based mathematical entities.

A sparse eligible pair set \(E\subseteq O\times F\) and candidate set \(C\) are Pyomo Set objects. Candidate tuples have six coordinates \((o,m,f,r,d,p)\). Ineligible combinations are excluded before variables are created. This is domain filtering, not a brute-force enumeration of complete schedules.

## H. Time representation

The configured days are Monday through Saturday. Twelve one-hour periods run from 07:30 to 19:30. The scenario stores thirteen boundaries; the interval between consecutive boundaries is one period. The mathematical time domain is \(T=D\times P\), represented through indexed start/occupancy groups rather than a database Timeslot entity or an additional Pyomo T object.

A duration-\(L_o\) meeting starting at \(p\) occupies every period:

\[
\{p,p+1,\ldots,p+L_o-1\}.
\]

For example, a three-period meeting beginning at P2 occupies P2, P3 and P4. Valid candidate starts satisfy \(1\le p\le |P|-L_o+1\). All occupancy constraints use the full interval. A meeting cannot wrap into another day. No lunch blackout, faculty availability calendar, half-hour period or day-specific preference is implemented.

## I. Runtime matrices and indexed parameters

The application builds numeric coefficients and categorical values from the saved scenario. They are Python dictionaries/lists used to construct linear expressions, not persisted matrix tables and not separate Pyomo Param components. This distinction reflects the actual model.

| Matrix / coefficient | Dimensions and values | Source and use |
|---|---|---|
| Faculty × Subject | faculty count × subject count; CANNOT/CAN/MUST_TEACH | Explicit rules, missing pairs treated as CANNOT; eligibility and mandatory teaching |
| Offering × Block | offering count × block count; 0/1 | CourseOfferingBlock attendance; block collision groups |
| Offering × Room compatibility | offering count × room count; 0/1 | Type equality and capacity ≥ expected students; candidate filtering |
| Offering × Time | offering × day × period; occupied-meeting counts | Reconstructed accepted starts; verifies offering occupancy |
| Faculty × Time | faculty × day × period; occupied-meeting counts | Full-duration coverage; must not exceed one |
| Room × Time | room × day × period; occupied-meeting counts | Full-duration coverage; must not exceed one |
| Block × Time | block × day × period; occupied-meeting counts | Attendance-linked full-duration coverage; must not exceed one |

Additional coefficients are expected_students, duration, meetings, room capacity, room type and maximum faculty load. The model's candidate construction enforces room compatibility, categorical eligibility and start boundaries. The independent validator reconstructs the four occupancy matrices after the solve and reports any count above one.

For the synthetic demonstration, the Faculty × Subject matrix is:

| Faculty | Foundations | Algorithms |
|---|---|---|
| DEMO-F1 | MUST_TEACH | CAN |
| DEMO-F2 | CANNOT | MUST_TEACH |

A 30-student lecture offering is compatible with the 30-seat and 40-seat lecture rooms, and incompatible with the 30-seat lab. Its room-compatibility row is [1,1,0] in that room order. A lab offering has [0,0,1]. For a section assigned to block A, the Offering × Block row contains 1 at A and 0 at the other blocks; users can explicitly associate additional blocks.

These matrices describe feasibility, not a hidden preference score. A CAN cell and a MUST_TEACH cell are categories with different logical effects; neither is assigned an arbitrary numerical reward.

## J. Actual decision variables

Two families of binary variables are implemented:

\[
x_{omfrdp}\in\{0,1\},\qquad (o,m,f,r,d,p)\in C,
\]

where 1 means that meeting \(m\) of offering \(o\) starts with faculty \(f\), room \(r\), day \(d\), period \(p\); and

\[
y_{of}\in\{0,1\},\qquad (o,f)\in E,
\]

where 1 identifies the faculty assigned to the offering across all of its meetings. The linking constraints make this common-faculty interpretation mandatory. They prevent different meetings of one offering from being inadvertently assigned to unrelated instructors.

Variables do not exist for CANNOT or absent-rule pairs. They also do not exist for incompatible rooms or invalid starts. The solver selects among valid start alternatives; Timble does not manually search complete permutations of schedules.

## K. Implemented hard constraints

Define \(C(o,m)\) as candidates for one meeting and \(C(o,m,f)\) as candidates additionally restricted to faculty \(f\). All sums below are over existing sparse candidates only.

### Meeting assignment and faculty consistency

\[
\sum_{c\in C(o,m)}x_c=1\quad\forall o,m.
\]

Every required meeting is scheduled exactly once. The model does not omit difficult offerings to improve its objective.

\[
\sum_{c\in C(o,m,f)}x_c=y_{of}\quad\forall(o,f)\in E,\ m=1,\ldots,M_o.
\]

Every meeting uses the same chosen faculty. Together with exact assignment, these equations imply exactly one eligible faculty per offering.

### Mandatory teaching

For a MUST_TEACH rule on faculty \(f\) and subject \(s\), with at least one matching offering in the scenario:

\[
\sum_{o:\operatorname{subject}(o)=s}y_{of}\ge1.
\]

The requirement is at least one offering, not all sections. If two faculty both have MUST_TEACH for a subject, the model must have enough distinct offerings to satisfy both while preserving one faculty per offering. If the subject has no offering in the scenario, no mandatory constraint is added.

### Resource and attendance collisions

Let \(U_f(d,q)\) contain candidate starts assigned to faculty \(f\) on day \(d\) whose duration interval covers period \(q\). Similarly define \(U_r(d,q)\) for rooms and \(U_b(d,q)\) for blocks attending the candidate offering. The implementation enforces:

\[
\sum_{c\in U_f(d,q)}x_c\le1,\qquad
\sum_{c\in U_r(d,q)}x_c\le1,\qquad
\sum_{c\in U_b(d,q)}x_c\le1.
\]

The faculty, room and block inequalities are constructed in separate modules. These constraints apply to every occupied period, including periods after a meeting's start. Independent tests isolate each resource type and produce an infeasible model when two meetings require its only available period.

### Maximum faculty teaching load

Let \(H_f\) be the maximum weekly load, interpreted as one-hour occupied periods:

\[
\sum_{o:(o,f)\in E} L_o M_o y_{of}\le H_f.
\]

Lecture and lab offerings contribute their own duration times weekly frequency. This constraint does not reinterpret academic units as workload. Institutional users must enter load values in the documented period unit.

### Distinct meeting days

\[
\sum_{m,f,r,p:(o,m,f,r,d,p)\in C}x_{omfrdp}\le1
\quad\forall o,d.
\]

An offering can have at most one of its meetings on a given day. This explicit revised policy makes weekly meeting frequency meaningful. An input requesting more meetings than configured days is rejected during model construction.

### Capacity, room type and duration domains

Candidates must satisfy \(\operatorname{capacity}_r\ge\operatorname{students}_o\), exact LAB/LECTURE compatibility, eligible faculty, and a valid consecutive-period interval. These restrictions are implemented by sparse candidate construction rather than redundant inequality rows. The same conditions are checked independently after the solve.

Inactive faculty and rooms are excluded. Inactive program, subject, curriculum or linked block data cause the scenario builder to reject affected offerings rather than silently generate a partial timetable. Every offered meeting must have at least one feasible candidate; a missing candidate is reported as an input/model error before invoking HiGHS. Infeasibility involving combinations of otherwise valid candidates is reported by the solver.

## L. Faculty teaching rules

CANNOT forbids a faculty/subject assignment. CAN permits candidates, subject to room, time, load and collision constraints. MUST_TEACH permits candidates and adds the minimum-one-offering inequality. Missing rules are treated conservatively as ineligible and displayed as CANNOT in the runtime matrix.

Rules are unique per faculty/subject pair and validated as categorical strings. Database checks also restrict the persisted category. The application does not derive a MUST_TEACH obligation from a preference number or automatically convert legacy expertise into an explicit permission. Those source records remain auditable review items until confirmed.

## M. Objective function

For every candidate, define nonnegative room waste:

\[
W_{or}=\operatorname{capacity}_r-\operatorname{students}_o.
\]

The actual objective in `optimization/objective.py` is:

\[
\min\sum_{(o,m,f,r,d,p)\in C} W_{or}x_{omfrdp}.
\]

Waste is counted once per scheduled meeting, not once per occupied period. The objective does not reward earlier days, preferred faculty, compact timetables or balanced room use. Such properties may arise incidentally but are not optimization claims. Multiple timetables can have the same minimum waste.

For the verified twelve-offering demonstration, Foundations contributes 20 unused seats across its four meetings; Algorithms lectures contribute 25 and labs contribute 25. Total room waste is 70. The independently reconstructed result agrees with the solver objective.

## N. Pyomo's role

Pyomo builds the actual algebraic model: 1-based RangeSets, sparse candidate sets, binary variables, ConstraintLists and a minimization Objective. The builder invokes separate assignment, faculty, room, block and duration modules. The completed ConcreteModel is passed to the APPSI Highs interface. Pyomo supplies the modeling and integration layer; HiGHS performs optimization.

The adapter requests that no solution be loaded automatically. It first checks whether a feasible objective is available, then loads variables only for a feasible result. This prevents an infeasible solve from being treated as an assignment. The use of feasible-objective and objective-bound values follows the documented [Pyomo APPSI result interface](https://pyomo.readthedocs.io/en/6.8.1/api/pyomo.contrib.appsi.base.Results.html).

## O. HiGHS solver and genuine measurements

Timble invokes `pyomo.contrib.appsi.solvers.Highs`, which uses the installed highspy library. The tested versions are Pyomo 6.10.1 and highspy 1.15.1. Configuration fixes one thread, random seed zero, relative MIP gap zero, and a 60-second solver time limit. Runtime measurements include model construction and solution extraction; the solver time limit itself does not include all of that surrounding work.

The adapter reads the best feasible objective and best objective bound from APPSI. It obtains native MIP gap and explored-node count from the HiGHS info structure. Non-finite measurements are stored as null and shown as unavailable. The native-info access uses the adapter's `_solver_model`; this integration detail is covered by real-solver tests and pinned dependency versions.

HiGHS uses branch-and-cut for mixed-integer problems. Conceptually, the solver branches on integer decisions, uses relaxation bounds to rule out unpromising subproblems, and uses valid cuts to tighten relaxations. These are solver capabilities, not algorithms separately implemented in Timble. This characterization follows the [official HiGHS solver documentation](https://ergo-code.github.io/HiGHS/dev/#Solvers).

The application distinguishes OPTIMAL, FEASIBLE_LIMIT, INFEASIBLE, NO_SOLUTION and ERROR outcomes. A feasible incumbent without proven optimal termination is accepted only as FEASIBLE_LIMIT. A missing incumbent produces no assignments. An unexpected exception records ERROR and its diagnostic; successful persistence is atomic.

## P. Defense answer: “What algorithm does the CSP use?”

Timble expresses the timetable as a binary mixed-integer linear optimization problem using Pyomo. HiGHS solves that model with its MIP solver. The system's contribution is the explicit formulation, academic-data transformation, validated constraints, objective, reproducible scenario and explanation interface. It does not contain a custom brute-force or custom backtracking timetable generator, and does not train a scheduling agent.

Calling the problem a CSP emphasizes its discrete choices and hard feasibility rules. Calling it a constraint optimization problem adds the room-waste minimization criterion. Both descriptions refer to the same implemented scheduling task; “CSP” is not the name of an additional solver module.

## Q. Optimization demonstration and assignment traceability

The Scheduling studio provides Timetable, Solver progress and Optimization computation views. The computation view shows Faculty × Subject, Offering × Block and Offering × Room compatibility matrices, followed by selectable-day Offering/Faculty/Room/Block × Time matrices. Matrix rows and columns display 1-based mathematical labels alongside meaningful academic labels.

For a selected final assignment, the explanation identifies the offering and expected students, lists every faculty category, lists room capacities and rejection reasons, names the chosen faculty and room, computes room waste, and enumerates occupied periods. The saved scenario, not mutable current master data, supplies these values. The explanation describes eligibility and global feasibility; it does not claim that an unmodeled preference caused a particular tie-breaking choice.

The independent result checker reports meeting completeness, categorical eligibility, same-faculty consistency, room capacity/type, period boundaries, duration, distinct days, faculty load, MUST_TEACH and all reconstructed collision counts. Tests also verify that editing a room after a run does not alter the saved explanation or original waste.

An interactive hypothetical collision duplicates the first accepted meeting in an illustrative occupancy table. Each covered faculty-period cell becomes 2, visibly violating the ≤1 condition. It is labeled hypothetical and never saved as a real assignment. The actual accepted timetable remains unchanged.

## R. Solver computation demonstration

The current integration exposes state changes while the worker runs, followed by one real terminal metric sample. It does not record intermediate incumbent callbacks or fabricate an iteration history. The interface explicitly states this limitation.

The fields displayed are objective value, best bound, MIP gap, search nodes and elapsed seconds. The verified browser run and MySQL workflow both produced objective 70, bound 70, gap 0 and one explored node. Measured runtime was approximately half a second on the execution machine; this isolated small example is not a benchmark for institutional-scale scheduling.

The original full measurement values are saved in `artifacts/verified-demo-run.json` and `artifacts/database-verification.json`. The browser interface rounds numeric display for readability, while persisted values retain their original precision. There are no training epochs or invented progress samples.


## S. Bulk management

Bulk Management accepts UTF-8 CSV files, with an optional byte-order mark. It requires the exact header order from a downloaded template. Every record is normalized, resolved against its related entities, and validated using the same Django models as CRUD. Subject resolution accepts a canonical code or a registered alias. Duplicate natural keys in a single file are row errors.

A preview runs all prospective writes within an outer transaction and rolls them back. This permits validation of the same effects that would occur during import, including sequential uniqueness checks, without retaining rows. Commit repeats validation and retains data only if every row succeeds. Per-row savepoints permit collecting multiple errors without leaving a transaction unusable. Errors include the source CSV row number; row 1 denotes a header error. Counts describe inserted, updated and unchanged records for a valid operation; when committed=false they are preview counts, not retained changes.

The formats below are drawn from the actual SCHEMAS registry. Subject has no stored failure-rate column, following the user's clarification.

### Programs

```csv
program_code,program_name,max_year_level,is_active
```

### Subjects

```csv
subject_code,subject_name,is_active
```

### Program Subjects

```csv
program_code,subject_code,year_level,units,lecture_periods,lab_periods,lecture_meetings_per_week,lab_meetings_per_week,lecture_room_type,lab_room_type,is_elective,is_active
```

### Prerequisites

```csv
program_code,subject_code,prerequisite_subject_code
```

### Block Sections

```csv
program_code,year_level,section_code,student_count,is_active
```

### Faculty

```csv
employee_code,first_name,middle_initial,last_name,faculty_type,max_teaching_load,is_active
```

### Faculty Teaching Rules

```csv
employee_code,subject_code,teaching_rule
```

### Rooms

```csv
room_code,room_type,capacity,is_active
```

### Subject Aliases

```csv
alias,subject_code
```

### Historical Enrollment

```csv
academic_year,program_code,subject_code,enrollment_count
```


Teaching-rule values are CANNOT, CAN and MUST_TEACH. Room values are LAB and LECTURE. Faculty types are FULL_TIME and PART_TIME. Boolean imports accept true/false or 1/0. Foreign keys use readable codes rather than old primary-key values. Missing required relationships are rejected rather than created with guessed academic attributes. The upload endpoint has a 10 MB limit. The new importer accepts normalized CSV, not arbitrary legacy spreadsheets or student rosters.

### Complete ZIP package import

The final Bulk Management interface defaults to one ZIP containing all ten revised CSV files. `services/bundle.py` processes programs, subjects, faculty, rooms, aliases, curriculum, prerequisites, blocks, teaching rules and annual history in dependency order. ZIP entry order is immaterial. Each file reuses the existing CSV validator, while an outer transaction guarantees package-wide atomicity. A preview rolls back all provisional changes. A failed commit rolls back earlier files and restores updated rows. A successful commit applies the package together.

The interface displays per-file validation status and insert/update/skip counts, followed by filename and row number for each error. Changing the file or import format clears previous validation approval. Download endpoints supply a complete template ZIP, the revised source package, and a separate synthetic demonstration package. The single-CSV download names match the ZIP’s canonical filenames.

Before decompression, the service checks the exact ten root members, duplicates, encryption flags and declared expanded sizes. It accepts at most 10 MB uploaded, 10 MB per CSV and 40 MB expanded in total. It reads members in memory without extracting paths. Unexpected folders or paths, missing files, damaged archives and invalid UTF-8 are rejected. Header-only files represent deliberately empty datasets, not fabricated data.

Twelve backend tests cover ZIP preview, dependency ordering, alias references in curriculum, commit/reimport idempotence, rollback of insertions and updates after a late error, malformed/missing/duplicate/unexpected members, expanded size, UTF-8 errors, source/template validity and authenticated endpoints. Two additional frontend tests cover the preview-to-commit interaction and invalidation when the selected ZIP changes. The browser test imports the synthetic package through this exact UI before forecasting and scheduling; the MySQL workflow also uses the bundle importer within a rollback-only outer transaction.

## T. Dataset revision and integrity

The transformation script reads `../Timble_/datasets/datasets.zip` and leaves the legacy project unchanged. The archive contains ten CSV files and no spreadsheet, historical-enrollment or block-section file. Each entry is decoded and inventoried with its columns, row count and SHA-256. The archive is extracted into a project-local temporary directory. The script rechecks the original archive hash after processing.

The revised archive contains exactly the ten requested new-schema CSV names. It is rebuilt from `datasets/source`, rather than copying or renaming the legacy archive. The separate synthetic demonstration package is not included. The revision report exists both at the root and inside `datasets`; these copies match.

Accepted real source records comprise 6 programs, 121 subjects, 18 faculty, 12 rooms and 40 aliases. Subject codes are derived from curriculum references to the same legacy identity. Where that identity has several unambiguous codes, the lexicographically first normalized code is canonical and the others become aliases. A code shared by conflicting identities is not arbitrarily assigned. Faculty import keys use LEGACY-F plus the old identity; these are explicitly not claimed to be institutional employee numbers. Room lab/lec values map to LAB/LECTURE as authorized by the user.

Current curricula are selected by the numerically latest effective_start for each program. The script flattens 361 current ProgramSubject candidates and retains 247 prerequisite expressions for review. Missing meeting-duration/frequency interpretation is not filled with guessed values. Textual prerequisites, duplicate program/subject identities, ambiguous subject codes and expertise rows without an explicit teaching category are preserved in the review package. There are 546 unresolved source rows in total. Source rows and candidate transformations can be inspected in `datasets/review/unresolved.json`, `program_subject_candidates.csv`, `prerequisite_candidates.csv` and `column_classification.csv`.

The five source outputs for curriculum, prerequisites, blocks, teaching rules and historical enrollment therefore have headers but no accepted rows. This is an explicit data-readiness limitation. Loose legacy rosters outside the archive were not silently merged: the annual count semantics and identity de-duplication policy must be established before those can be treated as normalized historical evidence. The system's CSV history importer and alias resolution are implemented and tested, but real annual counts are not invented from unverified files.

The original instruction mentioned subject failure rates and specialized lab categories. The user's clarification superseded those requirements: failure probability is an input assumption, and room categories are LAB/LECTURE. Consequently, absent historical rates do not block subject conversion. The remaining curriculum meeting-pattern question is still awaiting academic confirmation.

## U. Legacy and revised systems

| Inspected legacy concept | Actual revised implementation |
|---|---|
| Term-based records | Annual historical records and target academic year |
| Timeslot table | Configured day × one-hour-period domain |
| YearLevel entity | Positive integer bounded by program maximum |
| Several curriculum versions | One unique ProgramSubject per program/subject |
| Free-text prerequisite dependence | Validated same-program foreign-key graph |
| Faculty expertise and availability | Explicit CANNOT/CAN/MUST_TEACH; no availability table |
| Numeric preference or agent reward | Categorical hard rules and one room-waste objective |
| Custom timetable search / learning modules | Pyomo model and native HiGHS MIP solve |
| Mutable explanations coupled to current data | Persisted forecast evidence and schedule input snapshot |
| Legacy archive formats | Revised schema CSVs plus auditable unresolved records |
| Hidden assignment reasoning | Matrices, independent validation and per-assignment explanation |

The audit in `docs/LEGACY_AUDIT.md` classifies the relevant legacy elements as REUSE, REFACTOR or REMOVE. Reuse is limited primarily to the branding asset and visual identity. Core services and migrations were implemented afresh.

## V. Testing and validation

The final backend suite contains 51 tests. Master-data and import tests cover zero/excess year levels, categorical rules, the absence of a Subject failure-rate field, two room categories, exact headers, row-level errors, transaction rollback, preview behavior, idempotent updates, alias resolution, alias ambiguity, duplicate keys, authentication, CSRF and CRUD validation. Forecast tests cover the 100-to-95 computation, runtime probability changes, own-history fallback, missing history, invalid assumptions, MAX across prerequisites, cycle detection, finalization idempotence, missing-block rollback, inactive records, cross-program SUM, preserved component snapshots and invalid API input.

Solver tests use the actual Pyomo/HiGHS integration. They verify optimal objective and bound, CANNOT exclusion, MUST_TEACH satisfaction without all-section assignment, capacity/type filtering, complete consecutive occupancy, end-of-day boundaries, 1-based indices, separate faculty/room/block infeasibility cases, absent candidate handling, excessive duration, weekly load and detection of a deliberately corrupted result. The persistence test executes import, forecasting, finalization, solving and storage, then verifies that later room edits cannot rewrite the saved run's explanations.

Five frontend tests check 1-based time-matrix reconstruction, the hypothetical collision example, and validation-before-commit behavior with a row-level import error. The production frontend build passes. Static analysis passes, Django reports no system-check issues, and migration generation reports no model drift.

The real-browser test uses headless Microsoft Edge against disposable local servers and a separate SQLite database. It signs in, previews a ten-file ZIP without retaining rows, commits the ZIP, creates a record, generates and inspects a forecast, finalizes it, launches the asynchronous solver, verifies twelve timetable rows, opens explanations, displays every matrix, invokes the hypothetical collision, checks metrics and verifies the 390-pixel layout has no document overflow. No browser page errors occurred. Screenshots are retained under `artifacts`.

Fresh migrations and both CSV package validators were also executed on the configured MySQL database. A full workflow inside a rollback-only transaction achieved an optimal twelve-assignment result with objective 70 and gap zero, then left no demo data behind. The database account cannot create separate test schemas; therefore the full 51-test suite was run on SQLite, not misreported as a MySQL suite. An attempted MySQL test-schema creation was denied, and database privileges were not changed.

## W. Results and evaluation guidance

The demonstrated result establishes implementation correctness on a deterministic small fixture. It does not establish predictive accuracy or institution-scale solver performance. A suitable thesis evaluation should distinguish those questions.

For scheduling experiments, record input scope, active faculty/rooms/blocks, offering and meeting counts, duration distribution, candidate count where measured, termination status, assigned-meeting count, independently detected hard-constraint violations, objective, bound, gap, explored nodes and measured runtime. Report feasible time-limited outcomes separately from proven optima. Do not replace unavailable measurements with zero. A failed input precheck and a solver-proven infeasible case are different outcomes and should be analyzed separately.

For forecasting, report the prior-year source, prerequisite evidence, user-entered failure assumption, adjusted values, MAX selection, rounded demand, capacity and resulting sections. Where later actual annual counts become available, forecast-versus-actual errors may be evaluated in a future experiment. The current application does not calculate an accuracy metric, estimate failure probabilities, or supply a validated historical benchmark. A hypothetical probability cannot be described as an empirically measured institutional failure rate.

Before using the real curriculum for evaluation, resolve its meeting-pattern and prerequisite mappings, establish block records, confirm explicit teaching permissions and import authoritative annual counts. Retain the dataset audit as part of the experiment's provenance. The snapshot and result tables then permit reproduction of the precise optimization inputs independently of later master-data changes.

The measured synthetic result is: twelve required meetings assigned, zero independent hard-constraint violations, room waste 70, best bound 70, MIP gap zero and one explored node. Runtime varies by execution. These values can be reproduced with the separate demo package, with equal-cost timetable placements permitted to differ.

## X. Defense questions and answers

**Why is this a CSP or constraint optimization problem?** The timetable chooses discrete faculty, room, day and start alternatives under simultaneous hard restrictions. The room-waste objective selects among feasible combinations.

**Why Pyomo?** It gives the implementation an explicit algebraic model with separately readable variables, constraints and objective, instead of embedding the search in an opaque application loop.

**What does HiGHS do?** It solves the mixed-integer model and supplies genuine termination and quality measurements. Pyomo builds the model; HiGHS performs the search.

**What algorithm is used?** Timble formulates a binary MILP. HiGHS uses its MIP branch-and-cut solver. Timble does not implement a separate backtracking timetable algorithm.

**Where are the computations?** Forecast arithmetic is in `forecast_engine.py`; sparse candidates are in `optimization/variables.py`; constraint modules and `objective.py` define the algebra; `solver.py` invokes HiGHS; `domain/results.py` independently reconstructs validation and explanations.

**Why is Timeslot not a database table?** Days and period boundaries are configuration. A start plus duration determines all occupied periods, removing redundant stored slot combinations.

**What does Faculty × Time mean?** Each cell counts the meetings occupying a faculty member's particular day and period. A value above one is a conflict.

**What does Subject/Offering × Time mean?** Timble's implemented view is Offering × Time. A subject can have several section/component offerings; the offering row identifies the specific requirement and its occupied periods.

**Why remove FacultyExpertise?** Expertise does not unambiguously express permission or mandatory assignment. Explicit categorical teaching rules have direct mathematical effects.

**What are CANNOT, CAN and MUST_TEACH?** They respectively forbid assignment, permit assignment subject to all other constraints, and require at least one matching offering when such offerings exist.

**Why is YearLevel no longer master data?** The relevant information is an integer within each program's allowed range; a separate lookup table adds no necessary academic identity here.

**Why remove Semester?** The revised scope uses annual history and annual planning. The implementation does not claim that its annual aggregation is equivalent to the old term-based model.

**Why start indexing at 1?** The notation and displayed entities follow the specification's mathematical sets. Database IDs are remapped explicitly, and programming-array offsets are not exposed as mathematical labels.

**How are room conflicts detected?** Each chosen start contributes to all covered room/day/period cells, whose sums are constrained to at most one. The result validator recomputes those cells independently.

**How are faculty conflicts detected?** The same occupancy-sum restriction applies to faculty. Meeting-to-faculty linking also keeps one instructor across an offering's meetings.

**How are student-block conflicts detected?** Offering-block attendance links determine which block occupancy cells receive each meeting. Every attending block has its own at-most-one constraint.

**How does forecasting generate offerings?** Finalization splits integer demand into capacity-limited sections, creates every configured lecture/lab component, captures duration/frequency and links real blocks transactionally. It does not place timetable assignments on CourseOffering.

**How does the system show how a result was produced?** A run retains its exact scenario. The UI shows categorical rules, compatibility, attendance and occupancy matrices, objective arithmetic and candidate rejection reasons. The forecast view retains its source arithmetic separately.

**Is the failure assumption stored on Subject?** No. It is supplied to forecasting. The applied rate is preserved only as computation evidence for auditability.

**Does MUST_TEACH mean every section?** No. Its inequality requires at least one offering of that subject. Tests require two different mandatory faculty to receive different offerings when sufficient offerings exist.

**Is the timetable always optimal?** Only an OPTIMAL termination is presented as proven optimal under this model. A time-limited feasible result is labeled FEASIBLE_LIMIT with its available bound and gap.

**Does the system explain why a particular equally good time was chosen?** It explains feasibility and the modeled objective. It does not invent a preference or causal tie-break explanation where several equal-cost schedules exist.

**Are the real institutional datasets fully ready?** No. The accepted subset is validated, while uncertain curriculum, prerequisite, permission and missing annual-history/block records remain explicitly documented. The demonstration data are synthetic and labeled separately.

**What is not implemented?** Institutional-scale performance evidence, predictive-accuracy evaluation, automated probability estimation, arbitrary roster/spreadsheet ingestion, a supervised distributed task queue, live incumbent callbacks, cancellation, specialized room categories and role-specific permissions are not present. None is claimed in the results above.

## Implementation evidence and references

The primary evidence for application behavior is the code, initial migrations, tests, revised dataset report and saved synthetic run. `docs/DATABASE.md` enumerates actual model fields and relationships; `docs/VERIFICATION.md` records the executed checks. For the external solver's algorithm, see the [official HiGHS description](https://highs.dev/). For the result-interface contract, see the [Pyomo APPSI Results documentation](https://pyomo.readthedocs.io/en/6.8.1/api/pyomo.contrib.appsi.base.Results.html). These external references support library concepts; they do not substitute for validation of Timble's implementation.
