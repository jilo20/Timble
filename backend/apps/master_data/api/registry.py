from apps.forecasting.models import HistoricalEnrollment
from apps.master_data.models import (
    BlockSection,
    Faculty,
    FacultyTeachingRule,
    Program,
    ProgramSubject,
    ProgramSubjectPrerequisite,
    Room,
    Subject,
    SubjectAlias,
)

RESOURCES = {
    "programs": Program,
    "subjects": Subject,
    "program-subjects": ProgramSubject,
    "prerequisites": ProgramSubjectPrerequisite,
    "block-sections": BlockSection,
    "faculty": Faculty,
    "faculty-teaching-rules": FacultyTeachingRule,
    "rooms": Room,
    "subject-aliases": SubjectAlias,
    "historical-enrollment": HistoricalEnrollment,
}
