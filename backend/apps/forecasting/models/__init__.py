from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.validation import ValidatedModel, academic_year
from apps.master_data.models import BlockSection, Program, ProgramSubject, Subject


class HistoricalEnrollment(ValidatedModel):
    academic_year = models.CharField(max_length=9, validators=[academic_year])
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    enrollment_count = models.PositiveIntegerField()

    class Meta:
        db_table = "historical_enrollment"
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "program", "subject"], name="unique_history"
            )
        ]


class ForecastRun(ValidatedModel):
    academic_year = models.CharField(max_length=9, validators=[academic_year])
    status = models.CharField(
        max_length=16,
        choices=[("DRAFT", "Draft"), ("FINALIZED", "Finalized")],
        default="DRAFT",
    )
    section_capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forecasts_generated",
    )
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forecasts_finalized",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "forecast_run"


class ForecastResult(ValidatedModel):
    forecast_run = models.ForeignKey(ForecastRun, on_delete=models.CASCADE, related_name="results")
    program_subject = models.ForeignKey(ProgramSubject, on_delete=models.PROTECT)
    source_enrollment = models.PositiveIntegerField()
    failure_adjustment = models.DecimalField(max_digits=14, decimal_places=6)
    forecasted_students = models.PositiveIntegerField()
    required_sections = models.PositiveIntegerField()
    forecast_method = models.CharField(max_length=32)
    computation = models.JSONField(default=dict)  # Immutable evidence, not curriculum versioning.

    class Meta:
        db_table = "forecast_result"
        constraints = [
            models.UniqueConstraint(
                fields=["forecast_run", "program_subject"],
                name="unique_forecast_result",
            )
        ]


class CourseOffering(ValidatedModel):
    forecast_result = models.ForeignKey(
        ForecastResult, on_delete=models.PROTECT, related_name="offerings"
    )
    program_subject = models.ForeignKey(ProgramSubject, on_delete=models.PROTECT)
    section_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    expected_students = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    component_type = models.CharField(
        max_length=8, choices=[("LECTURE", "Lecture"), ("LAB", "Lab")]
    )
    duration_periods = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    meetings_per_week = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "course_offering"
        constraints = [
            models.UniqueConstraint(
                fields=["forecast_result", "section_number", "component_type"],
                name="unique_offering",
            )
        ]


class CourseOfferingBlock(ValidatedModel):
    course_offering = models.ForeignKey(
        CourseOffering, on_delete=models.CASCADE, related_name="block_links"
    )
    block_section = models.ForeignKey(BlockSection, on_delete=models.PROTECT)

    class Meta:
        db_table = "course_offering_block"
        constraints = [
            models.UniqueConstraint(
                fields=["course_offering", "block_section"],
                name="unique_offering_block",
            )
        ]
