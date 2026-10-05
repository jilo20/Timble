import csv
import io

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError, transaction

from apps.bulk_import.schema import KEYS, RESOURCES, SCHEMAS
from apps.core.validation import code
from apps.master_data.models import (
    Faculty,
    Program,
    ProgramSubject,
    Subject,
    SubjectAlias,
)


def resolve_subject(value):
    value = code(value)
    subject = Subject.objects.filter(subject_code=value).first()
    if subject:
        return subject
    alias = SubjectAlias.objects.select_related("subject").filter(alias=value).first()
    if alias:
        return alias.subject
    raise ValueError(f"Unknown subject: {value}")


def resolve_row(kind, row):
    values = {k: v.strip() for k, v in row.items()}
    for key in list(values):
        if key.endswith("_code") or key in [
            "alias",
            "teaching_rule",
            "room_type",
            "lecture_room_type",
            "lab_room_type",
            "faculty_type",
        ]:
            values[key] = code(values[key])
    if kind not in ["programs"] and "program_code" in values:
        values["program"] = Program.objects.get(program_code=values.pop("program_code"))
    if kind not in ["subjects"] and "subject_code" in values:
        values["subject"] = resolve_subject(values.pop("subject_code"))
    if kind not in ["faculty"] and "employee_code" in values:
        values["faculty"] = Faculty.objects.get(employee_code=values.pop("employee_code"))
    if kind == "prerequisites":
        values = {
            "program_subject": ProgramSubject.objects.get(
                program=values["program"], subject=values["subject"]
            ),
            "prerequisite_program_subject": ProgramSubject.objects.get(
                program=values["program"],
                subject=resolve_subject(values["prerequisite_subject_code"]),
            ),
        }
    for f in RESOURCES[kind]._meta.fields:
        if f.name in values and f.get_internal_type() == "BooleanField":
            token = values[f.name].lower()
            if token not in ["true", "false", "1", "0"]:
                raise ValueError(f"{f.name}: use true or false.")
            values[f.name] = token in ["true", "1"]
    return values


def import_csv(kind, content, commit=False):
    if kind not in SCHEMAS:
        raise ValueError("Unknown import type.")
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    expected = SCHEMAS[kind].split(",")
    if reader.fieldnames != expected:
        return {
            "valid": False,
            "errors": [{"row": 1, "message": "Headers must exactly match: " + SCHEMAS[kind]}],
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "committed": False,
        }
    counts = {"inserted": 0, "updated": 0, "skipped": 0}
    errors = []
    seen = set()
    with transaction.atomic():
        for number, row in enumerate(reader, 2):
            try:
                with transaction.atomic():
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError("Incorrect column count.")
                    values = resolve_row(kind, row)
                    identity = {k: values[k] for k in KEYS[kind]}
                    key = tuple(str(getattr(v, "pk", v)) for v in identity.values())
                    if key in seen:
                        raise ValueError("Duplicate natural key in this file.")
                    seen.add(key)
                    obj = RESOURCES[kind].objects.filter(**identity).first()
                    if obj:
                        before = {f.attname: getattr(obj, f.attname) for f in obj._meta.fields}
                        for k, v in values.items():
                            setattr(obj, k, v)
                        obj.full_clean()
                        changed = any(
                            before[f.attname] != getattr(obj, f.attname) for f in obj._meta.fields
                        )
                        if changed:
                            obj.save()
                            counts["updated"] += 1
                        else:
                            counts["skipped"] += 1
                    else:
                        RESOURCES[kind].objects.create(**values)
                        counts["inserted"] += 1
            except (
                ValueError,
                ValidationError,
                ObjectDoesNotExist,
                IntegrityError,
            ) as exc:
                errors.append({"row": number, "message": str(exc)})
        if errors or not commit:
            transaction.set_rollback(True)
    return {
        "valid": not errors,
        "errors": errors,
        **counts,
        "committed": bool(commit and not errors),
    }
