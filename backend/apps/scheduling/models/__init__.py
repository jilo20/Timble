from django.db import models

from apps.core.validation import ValidatedModel, academic_year
from apps.forecasting.models import CourseOffering
from apps.master_data.models import Faculty, Room


class ScheduleRun(ValidatedModel):
    academic_year = models.CharField(max_length=9, validators=[academic_year])
    solver_name = models.CharField(max_length=32, default="HiGHS")
    status = models.CharField(max_length=32, default="QUEUED")
    objective_value = models.FloatField(null=True, blank=True)
    best_bound = models.FloatField(null=True, blank=True)
    mip_gap = models.FloatField(null=True, blank=True)
    nodes_explored = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    elapsed_seconds = models.FloatField(null=True, blank=True)
    scenario_snapshot = models.JSONField(default=dict)
    diagnostic = models.TextField(blank=True)

    class Meta:
        db_table = "schedule_run"


class ScheduleAssignment(ValidatedModel):
    schedule_run = models.ForeignKey(
        ScheduleRun, on_delete=models.CASCADE, related_name="assignments"
    )
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.PROTECT)
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    meeting_number = models.PositiveSmallIntegerField()
    day_index = models.PositiveSmallIntegerField()
    start_period = models.PositiveSmallIntegerField()
    duration_periods = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "schedule_assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_run", "course_offering", "meeting_number"],
                name="unique_assignment",
            )
        ]


class SolverMetric(ValidatedModel):
    schedule_run = models.ForeignKey(ScheduleRun, on_delete=models.CASCADE, related_name="metrics")
    sequence_number = models.PositiveIntegerField()
    elapsed_seconds = models.FloatField()
    objective_value = models.FloatField(null=True, blank=True)
    best_bound = models.FloatField(null=True, blank=True)
    mip_gap = models.FloatField(null=True, blank=True)
    nodes_explored = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "solver_metric"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_run", "sequence_number"], name="unique_metric"
            )
        ]
