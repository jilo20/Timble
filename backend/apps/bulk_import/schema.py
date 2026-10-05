from apps.master_data.api.registry import RESOURCES as RESOURCES

SCHEMAS = {
    "programs": "program_code,program_name,max_year_level,is_active",
    "subjects": "subject_code,subject_name,is_active",
    "program-subjects": "program_code,subject_code,year_level,units,lecture_periods,lab_periods,lecture_meetings_per_week,lab_meetings_per_week,lecture_room_type,lab_room_type,is_elective,is_active",
    "prerequisites": "program_code,subject_code,prerequisite_subject_code",
    "block-sections": "program_code,year_level,section_code,student_count,is_active",
    "faculty": "employee_code,first_name,middle_initial,last_name,faculty_type,max_teaching_load,is_active",
    "faculty-teaching-rules": "employee_code,subject_code,teaching_rule",
    "rooms": "room_code,room_type,capacity,is_active",
    "subject-aliases": "alias,subject_code",
    "historical-enrollment": "academic_year,program_code,subject_code,enrollment_count",
}
KEYS = {
    "programs": ["program_code"],
    "subjects": ["subject_code"],
    "program-subjects": ["program", "subject"],
    "prerequisites": ["program_subject", "prerequisite_program_subject"],
    "block-sections": ["program", "year_level", "section_code"],
    "faculty": ["employee_code"],
    "faculty-teaching-rules": ["faculty", "subject"],
    "rooms": ["room_code"],
    "subject-aliases": ["alias"],
    "historical-enrollment": ["academic_year", "program", "subject"],
}
FILES = {
    "program-subjects": "program_subjects",
    "prerequisites": "program_subject_prerequisites",
    "block-sections": "block_sections",
    "faculty-teaching-rules": "faculty_teaching_rules",
    "subject-aliases": "subject_aliases",
    "historical-enrollment": "historical_enrollment",
}
