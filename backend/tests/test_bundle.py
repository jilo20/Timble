import io
import warnings
import zipfile
from unittest.mock import patch

from apps.bulk_import.services.bundle import IMPORT_ORDER, filename, import_bundle, package_bytes
from apps.forecasting.models import HistoricalEnrollment
from apps.master_data.models import Faculty, Program, ProgramSubject, Room, Subject
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase


def altered_package(changes=None, extra=None, omit=None, reverse=False):
    original = zipfile.ZipFile(io.BytesIO(package_bytes("demo")))
    content = {name: original.read(name) for name in original.namelist()}
    for name, value in (changes or {}).items():
        content[name] = value.encode("utf-8") if isinstance(value, str) else value
    if omit:
        content.pop(omit)
    content.update(extra or {})
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(content, reverse=reverse):
            archive.writestr(name, content[name])
    return result.getvalue()


class BundleTests(TestCase):
    def test_preview_dependency_order_without_retaining_rows(self):
        report = import_bundle(altered_package(reverse=True))
        self.assertTrue(report["valid"], report["errors"])
        self.assertFalse(report["committed"])
        self.assertEqual([r["file"] for r in report["files"]], [filename(k) for k in IMPORT_ORDER])
        self.assertEqual(Program.objects.count(), 0)
        self.assertEqual(HistoricalEnrollment.objects.count(), 0)
        self.assertEqual(len(report["files"]), 10)

    def test_commit_all_and_idempotent_repeat(self):
        report = import_bundle(package_bytes("demo"), True)
        self.assertTrue(report["committed"], report["errors"])
        self.assertEqual(ProgramSubject.objects.count(), 2)
        self.assertEqual(HistoricalEnrollment.objects.get().enrollment_count, 100)
        again = import_bundle(package_bytes("demo"), True)
        self.assertEqual(again["inserted"], 0)
        self.assertEqual(again["updated"], 0)
        self.assertEqual(again["skipped"], report["inserted"])

    def test_aliases_before_curriculum(self):
        with zipfile.ZipFile(io.BytesIO(package_bytes("demo"))) as archive:
            content = (
                archive.read("program_subjects.csv")
                .decode()
                .replace("DEMO-FOUND", "DEMO PROGRAMMING")
            )
        report = import_bundle(altered_package({"program_subjects.csv": content}), True)
        self.assertTrue(report["committed"], report["errors"])

    def test_late_error_rolls_back_all_insertions(self):
        text = "academic_year,program_code,subject_code,enrollment_count\n2025-2026,DEMO-CS,MISSING,100\n"
        report = import_bundle(altered_package({"historical_enrollment.csv": text}), True)
        self.assertFalse(report["valid"])
        self.assertFalse(report["committed"])
        self.assertEqual(report["errors"][0]["file"], "historical_enrollment.csv")
        self.assertEqual(report["errors"][0]["row"], 2)
        for model in [Program, Subject, ProgramSubject, Faculty, Room]:
            self.assertEqual(model.objects.count(), 0)

    def test_late_error_rolls_back_updates(self):
        import_bundle(package_bytes("demo"), True)
        subject = Subject.objects.get(subject_code="DEMO-FOUND")
        subject.subject_name = "Original"
        subject.save()
        report = import_bundle(
            altered_package({"historical_enrollment.csv": "wrong\nheader\n"}), True
        )
        self.assertFalse(report["committed"])
        subject.refresh_from_db()
        self.assertEqual(subject.subject_name, "Original")

    def test_invalid_archive_and_missing_member(self):
        for content in [b"not a zip", altered_package(omit="faculty.csv")]:
            report = import_bundle(content, True)
            self.assertFalse(report["valid"])
            self.assertEqual(report["inserted"], 0)

    def test_traversal_and_unexpected_members_rejected(self):
        for name in ["../escape.csv", "folder/rooms.csv", "extra.csv"]:
            report = import_bundle(altered_package(extra={name: b"test"}), True)
            self.assertFalse(report["valid"])
            self.assertIn("Unexpected", report["errors"][0]["message"])

    def test_duplicate_members_rejected(self):
        output = io.BytesIO(package_bytes("demo"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with zipfile.ZipFile(output, "a") as archive:
                archive.writestr("programs.csv", "duplicate")
        self.assertIn("duplicate", import_bundle(output.getvalue())["errors"][0]["message"])

    def test_expanded_size_limit(self):
        with patch("apps.bulk_import.services.bundle.MAX_EXPANDED_BYTES", 20):
            report = import_bundle(package_bytes("demo"), True)
        self.assertFalse(report["valid"])
        self.assertEqual(Program.objects.count(), 0)

    def test_invalid_utf8_rolls_back_and_names_file(self):
        report = import_bundle(altered_package({"historical_enrollment.csv": b"\xff\xfe"}), True)
        self.assertFalse(report["valid"])
        self.assertEqual(report["errors"][0]["file"], "historical_enrollment.csv")
        self.assertEqual(Program.objects.count(), 0)

    def test_actual_revised_archive_and_templates(self):
        for package in ["datasets", "templates"]:
            report = import_bundle(package_bytes(package))
            self.assertTrue(report["valid"], report["errors"])
            self.assertFalse(report["committed"])

    def test_authenticated_api_download_preview_commit(self):
        self.assertEqual(self.client.get("/api/bulk-bundle/").status_code, 403)
        user = get_user_model().objects.create_user("bundles")
        self.client.force_login(user)
        template = self.client.get("/api/bulk/program-subjects/")
        self.assertIn("program_subjects.csv", template["Content-Disposition"])
        template = self.client.get('/api/bulk/program-subjects/')
        self.assertIn('program_subjects.csv', template['Content-Disposition'])
        response = self.client.get("/api/bulk-bundle/?package=demo")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(len(archive.namelist()), 10)
        for commit in ["false", "true"]:
            response = self.client.post(
                "/api/bulk-bundle/",
                {
                    "file": SimpleUploadedFile(
                        "datasets.zip",
                        package_bytes("demo"),
                        "application/zip",
                    ),
                    "commit": commit,
                },
            )
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()["committed"], commit == "true")
        self.assertEqual(self.client.get("/api/bulk-bundle/?package=../../.env").status_code, 400)
