from apps.bulk_import.schema import SCHEMAS
from apps.bulk_import.services.importer import import_csv
from apps.forecasting.models import HistoricalEnrollment
from apps.master_data.models import (
    BlockSection,
    Faculty,
    FacultyTeachingRule,
    Program,
    Room,
    Subject,
    SubjectAlias,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase


class MasterDataTests(TestCase):
    def setUp(self):
        self.program = Program.objects.create(
            program_code="CS", program_name="Computer Science", max_year_level=4
        )
        self.subject = Subject.objects.create(subject_code="S1", subject_name="Foundations")

    def test_year_zero_and_exceeds_max(self):
        for year in [0, 5]:
            with self.assertRaises(ValidationError):
                BlockSection.objects.create(
                    program=self.program,
                    year_level=year,
                    section_code="A",
                    student_count=30,
                )

    def test_teaching_rules_categorical(self):
        f = Faculty.objects.create(
            employee_code="F",
            first_name="A",
            last_name="B",
            faculty_type="FULL_TIME",
            max_teaching_load=20,
        )
        with self.assertRaises(ValidationError):
            FacultyTeachingRule.objects.create(
                faculty=f, subject=self.subject, teaching_rule="PREFER"
            )
        for rule in ["CAN", "CANNOT", "MUST_TEACH"]:
            obj, _ = FacultyTeachingRule.objects.get_or_create(
                faculty=f, subject=self.subject, defaults={"teaching_rule": rule}
            )
            obj.teaching_rule = rule
            obj.save()

    def test_no_subject_failure_rate_field(self):
        self.assertNotIn("failing_rate", [f.name for f in Subject._meta.fields])

    def test_room_two_categories(self):
        for kind in ["LAB", "LECTURE"]:
            Room.objects.create(room_code=kind, room_type=kind, capacity=30)
        with self.assertRaises(ValidationError):
            Room.objects.create(room_code="X", room_type="UNKNOWN", capacity=30)

    def test_invalid_headers(self):
        result = import_csv("programs", "wrong\nhello\n", True)
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["row"], 1)

    def test_atomic_row_error(self):
        text = SCHEMAS["programs"] + "\nIT,Information Technology,4,true\nBAD,Bad,0,true\n"
        result = import_csv("programs", text, True)
        self.assertFalse(result["committed"])
        self.assertEqual(result["errors"][0]["row"], 3)
        self.assertFalse(Program.objects.filter(program_code="IT").exists())

    def test_preview_rolls_back(self):
        result = import_csv(
            "programs", SCHEMAS["programs"] + "\nIT,Information Technology,4,true\n"
        )
        self.assertTrue(result["valid"])
        self.assertFalse(Program.objects.filter(program_code="IT").exists())

    def test_idempotent_update_skip(self):
        text = SCHEMAS["programs"] + "\nCS,Updated name,4,true\n"
        self.assertEqual(import_csv("programs", text, True)["updated"], 1)
        self.assertEqual(import_csv("programs", text, True)["skipped"], 1)

    def test_alias_resolves_history(self):
        SubjectAlias.objects.create(alias="old s1", subject=self.subject)
        result = import_csv(
            "historical-enrollment",
            SCHEMAS["historical-enrollment"] + "\n2025-2026,CS,OLD S1,100\n",
            True,
        )
        self.assertTrue(result["valid"], result)
        self.assertEqual(HistoricalEnrollment.objects.get().subject, self.subject)

    def test_ambiguous_alias_rejected(self):
        other = Subject.objects.create(subject_code="OTHER", subject_name="Other")
        with self.assertRaises(ValidationError):
            SubjectAlias.objects.create(alias="s1", subject=other)

    def test_duplicate_keys_reported(self):
        result = import_csv("programs", SCHEMAS["programs"] + "\nA,A,4,true\nA,A,4,true\n", True)
        self.assertFalse(result["valid"])
        self.assertFalse(Program.objects.filter(program_code="A").exists())

    def test_revised_package_validates_without_import(self):
        before = Program.objects.count()
        call_command("validate_datasets", verbosity=0)
        self.assertEqual(Program.objects.count(), before)

    def test_authentication_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get("/api/programs/").status_code, 403)
        get_user_model().objects.create_user(username="tester", password="test-only-phrase")
        client.get("/api/session/")
        self.assertEqual(
            client.post(
                "/api/session/",
                data='{"username":"tester","password":"test-only-phrase"}',
                content_type="application/json",
            ).status_code,
            403,
        )
        token = client.cookies["csrftoken"].value
        response = client.post(
            "/api/session/",
            data='{"username":"tester","password":"test-only-phrase"}',
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN="http://127.0.0.1:5173",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get("/api/programs/").status_code, 200)

    def test_authenticated_crud_validation(self):
        user = get_user_model().objects.create_user("crud")
        self.client.force_login(user)
        response = self.client.post(
            "/api/block-sections/",
            data={
                "program": self.program.pk,
                "year_level": 0,
                "section_code": "A",
                "student_count": 30,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            "/api/programs/",
            data={
                "program_code": "IT",
                "program_name": "Information Technology",
                "max_year_level": 4,
                "is_active": True,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)
