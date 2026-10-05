from decimal import Decimal

from apps.forecasting.models import (
    CourseOffering,
    CourseOfferingBlock,
    ForecastRun,
    HistoricalEnrollment,
)
from apps.forecasting.services.forecast_engine import generate_forecast
from apps.forecasting.services.offering_generator import finalize_forecast
from apps.master_data.models import (
    BlockSection,
    Program,
    ProgramSubject,
    ProgramSubjectPrerequisite,
    Subject,
)
from apps.scheduling.services.scenario_builder import build_scenario
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase


class ForecastTests(TestCase):
    def setUp(self):
        call_command("load_demo", verbosity=0)
        self.user = get_user_model().objects.create_user("test")

    def forecast(self, rate="0.05"):
        return generate_forecast("2026-2027", 30, self.user, failure_rate=rate)

    def test_failure_and_sections(self):
        run = self.forecast()
        result = run.results.get(program_subject__subject__subject_code="DEMO-ALG")
        self.assertEqual(result.source_enrollment, 100)
        self.assertEqual(result.failure_adjustment, Decimal(5))
        self.assertEqual(result.forecasted_students, 95)
        self.assertEqual(result.required_sections, 4)
        self.assertEqual(result.computation["evidence"][0]["rate"], "0.05")

    def test_runtime_rate_changes_result(self):
        run = self.forecast("0.10")
        self.assertEqual(
            run.results.get(program_subject__subject__subject_code="DEMO-ALG").forecasted_students,
            90,
        )

    def test_no_prerequisite_uses_own_history(self):
        self.assertEqual(
            self.forecast()
            .results.get(program_subject__subject__subject_code="DEMO-FOUND")
            .forecasted_students,
            100,
        )

    def test_missing_history_is_not_zero(self):
        HistoricalEnrollment.objects.all().delete()
        with self.assertRaises(ValueError):
            self.forecast()
        self.assertEqual(ForecastRun.objects.count(), 0)

    def test_invalid_rate(self):
        for rate in ["-0.1", "1.1", "NaN", None]:
            with self.assertRaises(ValueError):
                self.forecast(rate)

    def test_max_of_adjusted_prerequisites(self):
        target = ProgramSubject.objects.get(subject__subject_code="DEMO-ALG")
        subject = Subject.objects.create(subject_code="THIRD", subject_name="Third")
        source = ProgramSubject.objects.create(
            program=target.program,
            subject=subject,
            year_level=1,
            units=1,
            lecture_periods=1,
            lab_periods=0,
            lecture_meetings_per_week=1,
            lab_meetings_per_week=0,
        )
        HistoricalEnrollment.objects.create(
            academic_year="2025-2026",
            program=target.program,
            subject=subject,
            enrollment_count=120,
        )
        ProgramSubjectPrerequisite.objects.create(
            program_subject=target, prerequisite_program_subject=source
        )
        self.assertEqual(
            self.forecast().results.get(program_subject=target).forecasted_students, 114
        )

    def test_cycle_rejected(self):
        a = ProgramSubject.objects.get(subject__subject_code="DEMO-FOUND")
        b = ProgramSubject.objects.get(subject__subject_code="DEMO-ALG")
        with self.assertRaises(ValidationError):
            ProgramSubjectPrerequisite.objects.create(
                program_subject=a, prerequisite_program_subject=b
            )

    def test_finalization_idempotent(self):
        run = self.forecast()
        finalize_forecast(run.pk, self.user)
        count = CourseOffering.objects.count()
        finalize_forecast(run.pk, self.user)
        self.assertEqual(count, 12)
        self.assertEqual(CourseOffering.objects.count(), 12)
        self.assertEqual(
            sum(
                CourseOffering.objects.filter(component_type="LAB").values_list(
                    "expected_students", flat=True
                )
            ),
            95,
        )
        self.assertEqual(CourseOfferingBlock.objects.count(), 12)

    def test_missing_blocks_atomic(self):
        BlockSection.objects.all().delete()
        run = self.forecast()
        with self.assertRaises(ValueError):
            finalize_forecast(run.pk, self.user)
        self.assertEqual(CourseOffering.objects.count(), 0)
        run.refresh_from_db()
        self.assertEqual(run.status, "DRAFT")

    def test_inactive_offering_source_rejected(self):
        run = self.forecast()
        finalize_forecast(run.pk, self.user)
        Subject.objects.filter(subject_code="DEMO-ALG").update(is_active=False)
        with self.assertRaises(ValueError):
            build_scenario(run.pk)

    def test_shared_subject_sum_api(self):
        p = Program.objects.create(program_code="OTHER", program_name="Other", max_year_level=4)
        subject = Subject.objects.get(subject_code="DEMO-FOUND")
        ProgramSubject.objects.create(
            program=p,
            subject=subject,
            year_level=1,
            units=1,
            lecture_periods=1,
            lab_periods=0,
            lecture_meetings_per_week=1,
            lab_meetings_per_week=0,
        )
        HistoricalEnrollment.objects.create(
            academic_year="2025-2026", program=p, subject=subject, enrollment_count=50
        )
        run = self.forecast()
        self.client.force_login(self.user)
        data = self.client.get(f"/api/forecasts/{run.pk}/").json()
        self.assertEqual(data["shared_subject_totals"]["DEMO-FOUND"], 150)

    def test_component_snapshot_survives_curriculum_edit(self):
        run = self.forecast()
        ProgramSubject.objects.filter(subject__subject_code="DEMO-ALG").update(
            lecture_periods=7, lecture_room_type="LAB"
        )
        finalize_forecast(run.pk, self.user)
        offering = CourseOffering.objects.filter(
            component_type="LECTURE", program_subject__subject__subject_code="DEMO-ALG"
        ).first()
        self.assertEqual(offering.duration_periods, 2)
        snapshot = build_scenario(run.pk)
        self.assertEqual(
            next(o for o in snapshot.offerings if o["id"] == offering.pk)["room_type"],
            "LECTURE",
        )

    def test_bad_api_input_returns_400(self):
        self.client.force_login(self.user)
        for path, data in [
            ("/api/forecasts/", {}),
            (
                "/api/forecasts/",
                {
                    "academic_year": "2026-2027",
                    "section_capacity": "bad",
                    "failure_rate": 0.05,
                },
            ),
            ("/api/schedules/", {"forecast_id": 9999}),
        ]:
            self.assertEqual(
                self.client.post(path, data=data, content_type="application/json").status_code,
                400,
            )
