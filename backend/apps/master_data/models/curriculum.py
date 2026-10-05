from django.core.exceptions import ValidationError
from django.db import models

from apps.core.validation import ValidatedModel, code

from .catalog import ROOM_TYPES, Program, Subject, positive


class ProgramSubject(ValidatedModel):
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    year_level = models.PositiveSmallIntegerField(validators=positive)
    units = models.PositiveSmallIntegerField()
    lecture_periods = models.PositiveSmallIntegerField()
    lab_periods = models.PositiveSmallIntegerField()
    lecture_meetings_per_week = models.PositiveSmallIntegerField()
    lab_meetings_per_week = models.PositiveSmallIntegerField()
    lecture_room_type = models.CharField(max_length=32, choices=ROOM_TYPES, default="LECTURE")
    lab_room_type = models.CharField(max_length=32, choices=ROOM_TYPES, default="LAB")
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.program_id and self.year_level and self.year_level > self.program.max_year_level:
            raise ValidationError({"year_level": "Exceeds the program maximum."})
        for kind in ["lecture", "lab"]:
            duration = getattr(self, kind + "_periods")
            meetings = getattr(self, kind + "_meetings_per_week")
            if bool(duration) != bool(meetings):
                raise ValidationError(
                    f"{kind}: duration and meeting count must both be zero or positive."
                )
        if not self.lecture_periods and not self.lab_periods:
            raise ValidationError("At least one instructional component is required.")

    class Meta:
        db_table = "program_subject"
        constraints = [
            models.UniqueConstraint(fields=["program", "subject"], name="unique_program_subject"),
            models.CheckConstraint(
                condition=models.Q(year_level__gte=1), name="curriculum_year_positive"
            ),
        ]


class ProgramSubjectPrerequisite(ValidatedModel):
    program_subject = models.ForeignKey(
        ProgramSubject, on_delete=models.CASCADE, related_name="prerequisites"
    )
    prerequisite_program_subject = models.ForeignKey(
        ProgramSubject, on_delete=models.PROTECT, related_name="dependents"
    )

    def clean(self):
        if not self.program_subject_id or not self.prerequisite_program_subject_id:
            return
        if self.program_subject.program_id != self.prerequisite_program_subject.program_id:
            raise ValidationError("Prerequisites must be in the same program.")
        frontier = [self.prerequisite_program_subject_id]
        seen = set()
        while frontier:
            current = frontier.pop()
            if current == self.program_subject_id:
                raise ValidationError("Prerequisite cycle detected.")
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(
                type(self)
                .objects.exclude(pk=self.pk)
                .filter(program_subject_id=current)
                .values_list("prerequisite_program_subject_id", flat=True)
            )

    class Meta:
        db_table = "program_subject_prerequisite"
        constraints = [
            models.UniqueConstraint(
                fields=["program_subject", "prerequisite_program_subject"],
                name="unique_prerequisite",
            )
        ]


class BlockSection(ValidatedModel):
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    year_level = models.PositiveSmallIntegerField(validators=positive)
    section_code = models.CharField(max_length=32)
    student_count = models.PositiveIntegerField(validators=positive)
    is_active = models.BooleanField(default=True)

    def clean(self):
        self.section_code = code(self.section_code)
        if self.program_id and self.year_level and self.year_level > self.program.max_year_level:
            raise ValidationError({"year_level": "Exceeds the program maximum."})

    class Meta:
        db_table = "block_section"
        constraints = [
            models.UniqueConstraint(
                fields=["program", "year_level", "section_code"], name="unique_block"
            ),
            models.CheckConstraint(
                condition=models.Q(year_level__gte=1), name="block_year_positive"
            ),
        ]
