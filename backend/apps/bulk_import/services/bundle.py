"""Validate/import the complete CSV package in one transaction, without extracting files."""

import csv
import io
import zipfile
import zlib

from django.conf import settings
from django.db import transaction

from apps.bulk_import.schema import FILES, SCHEMAS

from .importer import import_csv

# Aliases must exist before any curriculum/history file references them.
IMPORT_ORDER = (
    "programs",
    "subjects",
    "faculty",
    "rooms",
    "subject-aliases",
    "program-subjects",
    "prerequisites",
    "block-sections",
    "faculty-teaching-rules",
    "historical-enrollment",
)
MAX_ARCHIVE_BYTES = 10 * 1024 * 1024
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_EXPANDED_BYTES = 40 * 1024 * 1024


def filename(kind):
    return FILES.get(kind, kind) + ".csv"


def package_bytes(package="templates"):
    """Only fixed project-owned directories are downloadable; no request path is used."""
    if package not in ["templates", "datasets", "demo"]:
        raise ValueError("Unknown package. Choose templates, datasets or demo.")
    source = settings.BASE_DIR.parent / "datasets" / ("demo" if package == "demo" else "source")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for kind in IMPORT_ORDER:
            content = (
                (SCHEMAS[kind] + "\n").encode("utf-8")
                if package == "templates"
                else (source / filename(kind)).read_bytes()
            )
            archive.writestr(filename(kind), content)
    return output.getvalue()


def read_package(content):
    """Inspect limits, duplicate names and exact root members before decompressing."""
    if len(content) > MAX_ARCHIVE_BYTES:
        raise ValueError("ZIP upload exceeds 10 MB.")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            expected = {filename(kind) for kind in IMPORT_ORDER}
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise ValueError("ZIP contains duplicate filenames.")
            missing = sorted(expected - set(names))
            unexpected = sorted(set(names) - expected)
            if missing or unexpected:
                details = []
                if missing:
                    details.append("Missing: " + ", ".join(missing))
                if unexpected:
                    details.append("Unexpected: " + ", ".join(unexpected))
                raise ValueError(
                    "ZIP must contain the ten template CSV files at its root. " + "; ".join(details)
                )
            if any(entry.flag_bits & 1 for entry in entries):
                raise ValueError("Encrypted ZIP files are not supported.")
            if (
                any(entry.file_size > MAX_FILE_BYTES for entry in entries)
                or sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES
            ):
                raise ValueError("Expanded ZIP exceeds the limit: 10 MB per CSV, 40 MB total.")
            # Read by validated ZipInfo without creating filesystem paths.
            return {entry.filename: archive.read(entry) for entry in entries}
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, zlib.error) as exc:
        raise ValueError("Invalid, damaged or unsupported ZIP archive.") from exc


def import_bundle(content, commit=False):
    report = {
        "valid": False,
        "committed": False,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "files": [],
        "errors": [],
    }
    try:
        members = read_package(content)
    except ValueError as exc:
        report["errors"].append({"file": "ZIP package", "row": None, "message": str(exc)})
        return report
    with transaction.atomic():
        for kind in IMPORT_ORDER:
            name = filename(kind)
            try:
                # Inner writes are provisional until the outer package transaction commits.
                with transaction.atomic():
                    result = import_csv(kind, members[name], commit=True)
            except (UnicodeDecodeError, csv.Error) as exc:
                result = {
                    "valid": False,
                    "inserted": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": [{"row": None, "message": "Invalid UTF-8 CSV: " + str(exc)}],
                }
            report["files"].append(
                {
                    "file": name,
                    "valid": result["valid"],
                    **{key: result[key] for key in ["inserted", "updated", "skipped"]},
                }
            )
            for key in ["inserted", "updated", "skipped"]:
                report[key] += result[key]
            report["errors"].extend({"file": name, **error} for error in result["errors"])
        report["valid"] = not report["errors"]
        report["committed"] = bool(commit and report["valid"])
        if not report["committed"]:
            transaction.set_rollback(True)
    return report
