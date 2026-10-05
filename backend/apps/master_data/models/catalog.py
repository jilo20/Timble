from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.validation import ValidatedModel, code

ROOM_TYPES = [("LECTURE", "Lecture"), ("LAB", "Laboratory")]
RULES = [(v, v) for v in ["CANNOT", "CAN", "MUST_TEACH"]]
positive = [MinValueValidator(1)]


class Program(ValidatedModel):
    program_code = models.CharField(max_length=32, unique=True)
    program_name = models.CharField(max_length=255)
    max_year_level = models.PositiveSmallIntegerField(validators=positive)
    is_active = models.BooleanField(default=True)

    def clean(self):
        self.program_code = code(self.program_code)

    class Meta:
        db_table = "program"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_year_level__gte=1), name="program_year_positive"
            )
        ]


class Subject(ValidatedModel):
    subject_code = models.CharField(max_length=64, unique=True)
    subject_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def clean(self):
        self.subject_code = code(self.subject_code)
        if (
            SubjectAlias.objects.filter(alias=self.subject_code)
            .exclude(subject_id=self.pk)
            .exists()
        ):
            raise ValidationError({"subject_code": "Code conflicts with an existing alias."})

    class Meta:
        db_table = "subject"


class Faculty(ValidatedModel):
    employee_code = models.CharField(max_length=64, unique=True)
    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=10, blank=True)
    last_name = models.CharField(max_length=100)
    faculty_type = models.CharField(
        max_length=32, choices=[("FULL_TIME", "Full time"), ("PART_TIME", "Part time")]
    )
    max_teaching_load = models.PositiveSmallIntegerField(validators=positive)
    is_active = models.BooleanField(default=True)

    def clean(self):
        self.employee_code = code(self.employee_code)

    class Meta:
        db_table = "faculty"


class FacultyTeachingRule(ValidatedModel):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    teaching_rule = models.CharField(max_length=10, choices=RULES)

    class Meta:
        db_table = "faculty_teaching_rule"
        constraints = [
            models.UniqueConstraint(fields=["faculty", "subject"], name="unique_faculty_rule"),
            models.CheckConstraint(
                condition=models.Q(teaching_rule__in=["CANNOT", "CAN", "MUST_TEACH"]),
                name="categorical_rule",
            ),
        ]


class Room(ValidatedModel):
    room_code = models.CharField(max_length=32, unique=True)
    room_type = models.CharField(max_length=32, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField(validators=positive)
    is_active = models.BooleanField(default=True)

    def clean(self):
        self.room_code = code(self.room_code)

    class Meta:
        db_table = "room"


class SubjectAlias(ValidatedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    alias = models.CharField(max_length=64, unique=True)

    def clean(self):
        self.alias = code(self.alias)
        if Subject.objects.filter(subject_code=self.alias).exclude(pk=self.subject_id).exists():
            raise ValidationError({"alias": "Alias conflicts with a canonical subject code."})

    class Meta:
        db_table = "subject_alias"
