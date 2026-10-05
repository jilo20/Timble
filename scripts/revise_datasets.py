"""Reproducible archive transformation. Never opens the legacy database or writes to it."""

import csv
import hashlib
import io
import json
import os
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from apps.bulk_import.schema import FILES, SCHEMAS


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def export(path, headers, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


def main():
    archive = ROOT.parent / "Timble_" / "datasets" / "datasets.zip"
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    destination = ROOT / "datasets"
    extracted = ROOT / ".work" / "legacy_archive"
    extracted.mkdir(parents=True, exist_ok=True)
    inventory = []
    tables = {}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.lower().endswith(".csv"):
                raise ValueError("Unexpected archive entry: " + name)
            payload = z.read(name)
            text = payload.decode("utf-8-sig")
            (extracted / Path(name).name).write_text(text, encoding="utf-8")
            table = rows(text)
            tables[name] = table
            inventory.append(
                {
                    "file": name,
                    "rows": len(table),
                    "columns": list(table[0]) if table else [],
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )

    def get(label):
        return tables["Dataset - " + label + ".csv"]

    output = {kind: [] for kind in SCHEMAS}
    review = []
    for p in get("Programs"):
        output["programs"].append(
            {
                **{k: p[k] for k in ["program_code", "program_name", "max_year_level"]},
                "is_active": "true",
            }
        )
    for f in get("Faculty"):
        output["faculty"].append(
            {
                "employee_code": "LEGACY-F-" + f["faculty_id"],
                **{
                    k: f[k]
                    for k in [
                        "first_name",
                        "middle_initial",
                        "last_name",
                        "max_teaching_load",
                    ]
                },
                "faculty_type": f["faculty_type"].upper().replace(" ", "_").replace("-", "_"),
                "is_active": str(f["status"].lower() == "active").lower(),
            }
        )
    for r in get("Room"):
        output["rooms"].append(
            {
                "room_code": r["room_name"],
                "room_type": "LECTURE" if r["room_type"] == "lec" else "LAB",
                "capacity": r["capacity"],
                "is_active": str(r["status"].lower() == "active").lower(),
            }
        )
    latest = {}
    for c in get("Curriculum"):
        old = latest.get(c["program_id"])
        if old is None or int(c["effective_start"]) > int(old["effective_start"]):
            latest[c["program_id"]] = c
    current_ids = {c["curriculum_id"]: c for c in latest.values()}
    codes = defaultdict(set)
    for cs in get("curriculum_subject"):
        codes[cs["subject_id"]].add(" ".join(cs["subject_code"].upper().split()))
    code_owners = defaultdict(set)
    for sid, variants in codes.items():
        for variant in variants:
            code_owners[variant].add(sid)
    accepted_subject_ids = set()
    for s in get("subjects"):
        variants = sorted(codes[s["subject_id"]])
        if not variants or any(len(code_owners[c]) > 1 for c in variants):
            review.append(
                {
                    "source": "subjects",
                    "key": s["subject_id"],
                    "reason": "Missing or ambiguous subject code",
                    "row": s,
                    "candidate_codes": variants,
                }
            )
            continue
        canonical = variants[0]
        accepted_subject_ids.add(s["subject_id"])
        output["subjects"].append(
            {
                "subject_code": canonical,
                "subject_name": s["subject_name"],
                "is_active": s["is_active"].lower(),
            }
        )
        for alias in variants[1:]:
            output["subject-aliases"].append({"alias": alias, "subject_code": canonical})
    candidates = []
    candidate_prerequisites = []
    seen = set()
    for cs in get("curriculum_subject"):
        if cs["curriculum_id"] not in current_ids:
            continue
        curriculum = current_ids[cs["curriculum_id"]]
        program = curriculum["program_code"]
        subject = " ".join(cs["subject_code"].upper().split())
        candidate = {k: "" for k in SCHEMAS["program-subjects"].split(",")}
        candidate.update(
            program_code=program,
            subject_code=subject,
            year_level=cs["year_level_id"],
            units=cs["units"],
            is_elective=str(cs["requirement_type"] != "FIXED_SUBJECT").lower(),
            is_active=str(cs["status"].lower() == "active").lower(),
        )
        candidates.append(candidate)
        reasons = [
            "Missing verified duration and meetings-per-week; original weekly contact values retained for review"
        ]
        key = (program, subject)
        if key in seen:
            reasons.append("Duplicate current program/subject key requires resolution")
        seen.add(key)
        review.append(
            {
                "source": "curriculum_subject",
                "key": cs["curriculum_subject_id"],
                "reason": "; ".join(reasons),
                "row": cs,
                "candidate": candidate,
            }
        )
        prerequisite = cs["prerequisite_text"].strip()
        if prerequisite.lower() not in ["", "none", "n/a"]:
            candidate_prerequisites.append(
                {
                    "program_code": program,
                    "subject_code": subject,
                    "source_prerequisite_text": prerequisite,
                    "status": "MANUAL_REVIEW",
                }
            )
    for r in get("FacultyExpertise"):
        review.append(
            {
                "source": "FacultyExpertise",
                "key": r["expertise_id"],
                "reason": "Expertise is not an explicit CANNOT/CAN/MUST_TEACH permission; manual confirmation required",
                "row": r,
            }
        )
    for kind, data in output.items():
        export(
            destination / "source" / ((FILES.get(kind, kind)) + ".csv"),
            SCHEMAS[kind].split(","),
            data,
        )
    export(
        destination / "review" / "program_subject_candidates.csv",
        SCHEMAS["program-subjects"].split(","),
        candidates,
    )
    export(
        destination / "review" / "prerequisite_candidates.csv",
        ["program_code", "subject_code", "source_prerequisite_text", "status"],
        candidate_prerequisites,
    )
    (destination / "review" / "unresolved.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (destination / "review" / "archive_inventory.json").write_text(
        json.dumps(inventory, indent=2), encoding="utf-8"
    )
    with zipfile.ZipFile(destination / "datasets.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for file in sorted((destination / "source").glob("*.csv")):
            z.write(file, file.name)
    report = [
        "# Dataset revision report",
        "",
        f"Original archive: `../Timble_/datasets/datasets.zip`. SHA-256: `{digest}`.",
        "All ten archive CSVs were extracted into `.work/legacy_archive`, parsed, and inventoried. No spreadsheets or historical enrollment files are present in this archive. Other loose legacy rosters are not silently merged: annual counting and identity de-duplication would require a separately validated mapping.",
        "",
        "## Per-file and per-column classification",
        "",
        "| Original | New | KEEP | TRANSFORM / DERIVE | REMOVE |",
        "|---|---|---|---|---|",
        "| Programs | programs.csv | program_code, program_name, max_year_level | is_active=true: administrative import status | program_id |",
        "| subjects | subjects.csv and review | subject_name, is_active | canonical code from curriculum; lexicographic choice among same-identity aliases; conflicting identities held | subject_id, subject_description |",
        "| Curriculum | review/current candidates | program_code | latest by effective_start per program | curriculum_id, effective_end, program_id after flattening |",
        "| curriculum_subject | review/program_subject_candidates.csv | subject_code, units | year_level_id to integer; status to is_active; requirement_type to elective candidate | source IDs, old term IDs, subject type, elective_group_id; names are retained in review only |",
        "| Faculty | faculty.csv | names, max_teaching_load | LEGACY-F-{id} import key; normalized faculty_type; status to boolean | faculty_id, availability_status |",
        "| FacultyExpertise | review/unresolved.json | full original row for review only | no automatic permission mapping | expertise/name redundancy from runtime |",
        "| Room | rooms.csv | capacity | room_name to room_code; lec to LECTURE and lab to LAB per user clarification; status boolean | none silently discarded |",
        "| year_level | integer fields | order values for cross-checking | IDs 1â€“4 equal documented year order | master table, status and label |",
        "| semester | none | none | none | all columns |",
        "| Timeslot | none | none | none | all columns |",
        "",
        "## Counts and validation scope",
        "",
    ]
    report.extend(f"- {FILES.get(k, k)}.csv: {len(v)} accepted rows." for k, v in output.items())
    report += [
        "",
        f"{len(review)} unresolved source rows are retained with reasons in `review/unresolved.json`. {len(candidates)} current curriculum candidates were flattened; {len(candidate_prerequisites)} prerequisite expressions require mapping. Header-only outputs are deliberate, not evidence of completed academic data.",
        "",
        "## Assumptions and missing information",
        "- Program active status is an administrative default because the source has no status.",
        "- LEGACY-F identifiers preserve source identity and are not institutional employee numbers.",
        "- User clarification authorizes two room categories: LAB and LECTURE; all source rooms map directly.",
        "- User clarification: no subject failure-rate master field. Failure probability is entered at forecast generation; only calculation evidence retains the assumption used.",
        "- lec_hours/lab_hours cannot establish duration per meeting and weekly meeting count; candidates retain their original values in the review JSON.",
        "- Latest curriculum is selected by numeric effective_start. Duplicate program/subject candidates remain in review rather than being arbitrarily merged.",
        "- No block sections or historical enrollments were present in the archive. Those outputs contain headers only. Subject aliases derive from alternate curriculum codes for the same legacy subject identity.",
        "- Textual prerequisites are preserved for manual mapping, not interpreted as arbitrary AND/OR rules.",
        "- Explicit teaching permission must be confirmed for all expertise records.",
        "",
        "## Reproduce",
        "`python scripts/revise_datasets.py`, then `python backend/manage.py validate_datasets`. The validator uses the same transactional importer as the UI and rolls all changes back. The separate `datasets/demo` package contains synthetic, labeled defense examples and is never included in datasets.zip.",
        "",
        "The revised archive contains only the ten new schema CSVs. The legacy archive is read-only and its hash is rechecked after transformation.",
    ]
    classifications = []
    for entry in inventory:
        filename = entry["file"]
        for column in entry["columns"]:
            action = "KEEP"
            note = "Preserved verbatim in audit/review evidence."
            if filename.endswith(("semester.csv", "Timeslot.csv")):
                action = "REMOVE"
                note = "Obsolete entity excluded from all revised runtime datasets."
            elif column in [
                "availability_status",
                "subject_description",
                "elective_group_id",
                "semester_id",
            ]:
                action = "REMOVE"
                note = "Excluded from revised runtime schema; original retained in audit when relevant."
            elif column in [
                "program_id",
                "subject_id",
                "curriculum_id",
                "faculty_id",
                "year_level_id",
            ]:
                action = "TRANSFORM"
                note = "Resolve source relationship, flatten current curriculum, or derive documented stable import key; source IDs are not new database IDs."
            elif column in ["status", "faculty_type", "room_name", "room_type"]:
                action = "TRANSFORM"
                note = "Normalize controlled values, boolean activity, or renamed room_code."
            elif column == "effective_start":
                action = "DERIVE"
                note = "Select the numerically latest source curriculum for each program."
            elif column in [
                "effective_end",
                "curriculum_subject_id",
                "expertise_id",
                "year_level_name",
                "year_level_order",
            ]:
                action = "REMOVE"
                note = "Not a revised runtime field; retained in review or source inventory where needed."
            elif column in ["lec_hours", "lab_hours", "prerequisite_text", "requirement_type"]:
                action = "KEEP"
                note = "Retain as review evidence/candidate; academic mapping is not confirmed."
            classifications.append(
                {
                    "original_dataset": filename,
                    "column": column,
                    "classification": action,
                    "disposition": note,
                }
            )
    export(
        destination / "review" / "column_classification.csv",
        ["original_dataset", "column", "classification", "disposition"],
        classifications,
    )
    report += [
        "",
        "Every original column is separately classified in `datasets/review/column_classification.csv`. KEEP in review is not a claim that a field was accepted into runtime data.",
    ]
    report += [
        "",
        "## Single-package import",
        "Upload `datasets.zip` through Bulk Management → Dataset ZIP (all files). The application validates the ten files in dependency order and commits them atomically. The archive contains the verified subset; header-only outputs still represent unresolved or absent source data. `demo-datasets.zip` is a separate synthetic package and is not mixed into the revised real datasets.",
    ]
    text = "\n".join(report) + "\n"
    (destination / "DATASET_REVISION_REPORT.md").write_text(text, encoding="utf-8")
    (ROOT / "DATASET_REVISION_REPORT.md").write_text(text, encoding="utf-8")
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == digest
    print(
        json.dumps(
            {
                "accepted": {k: len(v) for k, v in output.items()},
                "review_rows": len(review),
                "current_candidates": len(candidates),
            }
        )
    )


if __name__ == "__main__":
    main()
