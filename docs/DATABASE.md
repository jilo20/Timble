# Actual database schema

Generated from registered Django models after passing tests. Each model has fresh migrations. Field lists below are the actual Python field names; foreign-key columns use Django’s `_id` suffix.

## auth_permission

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| name | CharField | — |
| content_type | ForeignKey | django_content_type |
| codename | CharField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## auth_group_permissions

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| group | ForeignKey | auth_group |
| permission | ForeignKey | auth_permission |

Constraints: Field-level uniqueness and validation as declared in the model.

## auth_group

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| name | CharField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## auth_user_groups

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| user | ForeignKey | auth_user |
| group | ForeignKey | auth_group |

Constraints: Field-level uniqueness and validation as declared in the model.

## auth_user_user_permissions

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| user | ForeignKey | auth_user |
| permission | ForeignKey | auth_permission |

Constraints: Field-level uniqueness and validation as declared in the model.

## auth_user

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| password | CharField | — |
| last_login | DateTimeField (nullable) | — |
| is_superuser | BooleanField | — |
| username | CharField | — |
| first_name | CharField | — |
| last_name | CharField | — |
| email | CharField | — |
| is_staff | BooleanField | — |
| is_active | BooleanField | — |
| date_joined | DateTimeField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## django_content_type

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| id | AutoField | — |
| app_label | CharField | — |
| model | CharField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## django_session

Django authentication, authorization, session or content-type infrastructure.

| Field | Type | Relationship / choices |
|---|---|---|
| session_key | CharField | — |
| session_data | TextField | — |
| expire_date | DateTimeField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## program

Program identity and maximum year.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| program_code | CharField | — |
| program_name | CharField | — |
| max_year_level | PositiveSmallIntegerField | — |
| is_active | BooleanField | — |

Constraints: <CheckConstraint: condition=(AND: ('max_year_level__gte', 1)) name='program_year_positive'>

## subject

Canonical subject identity; no stored failure probability.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| subject_code | CharField | — |
| subject_name | CharField | — |
| is_active | BooleanField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## faculty

Instructor identity and maximum weekly period load.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| employee_code | CharField | — |
| first_name | CharField | — |
| middle_initial | CharField | — |
| last_name | CharField | — |
| faculty_type | CharField | FULL_TIME, PART_TIME |
| max_teaching_load | PositiveSmallIntegerField | — |
| is_active | BooleanField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## faculty_teaching_rule

Categorical faculty/subject eligibility and obligation.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| faculty | ForeignKey | faculty |
| subject | ForeignKey | subject |
| teaching_rule | CharField | CANNOT, CAN, MUST_TEACH |

Constraints: <UniqueConstraint: fields=('faculty', 'subject') name='unique_faculty_rule'>; <CheckConstraint: condition=(AND: ('teaching_rule__in', ['CANNOT', 'CAN', 'MUST_TEACH'])) name='categorical_rule'>

## room

LAB/LECTURE room capacity.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| room_code | CharField | — |
| room_type | CharField | LECTURE, LAB |
| capacity | PositiveIntegerField | — |
| is_active | BooleanField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## subject_alias

Alternative normalized code resolving to a canonical subject.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| subject | ForeignKey | subject |
| alias | CharField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## program_subject

Current curriculum membership and component meeting requirements.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| program | ForeignKey | program |
| subject | ForeignKey | subject |
| year_level | PositiveSmallIntegerField | — |
| units | PositiveSmallIntegerField | — |
| lecture_periods | PositiveSmallIntegerField | — |
| lab_periods | PositiveSmallIntegerField | — |
| lecture_meetings_per_week | PositiveSmallIntegerField | — |
| lab_meetings_per_week | PositiveSmallIntegerField | — |
| lecture_room_type | CharField | LECTURE, LAB |
| lab_room_type | CharField | LECTURE, LAB |
| is_elective | BooleanField | — |
| is_active | BooleanField | — |

Constraints: <UniqueConstraint: fields=('program', 'subject') name='unique_program_subject'>; <CheckConstraint: condition=(AND: ('year_level__gte', 1)) name='curriculum_year_positive'>

## program_subject_prerequisite

Same-program directed prerequisite edge.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| program_subject | ForeignKey | program_subject |
| prerequisite_program_subject | ForeignKey | program_subject |

Constraints: <UniqueConstraint: fields=('program_subject', 'prerequisite_program_subject') name='unique_prerequisite'>

## block_section

Student attendance group.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| program | ForeignKey | program |
| year_level | PositiveSmallIntegerField | — |
| section_code | CharField | — |
| student_count | PositiveIntegerField | — |
| is_active | BooleanField | — |

Constraints: <UniqueConstraint: fields=('program', 'year_level', 'section_code') name='unique_block'>; <CheckConstraint: condition=(AND: ('year_level__gte', 1)) name='block_year_positive'>

## historical_enrollment

Observed prior-year program/subject count.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| academic_year | CharField | — |
| program | ForeignKey | program |
| subject | ForeignKey | subject |
| enrollment_count | PositiveIntegerField | — |

Constraints: <UniqueConstraint: fields=('academic_year', 'program', 'subject') name='unique_history'>

## forecast_run

Generation/finalization lifecycle and actors.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| academic_year | CharField | — |
| status | CharField | DRAFT, FINALIZED |
| section_capacity | PositiveIntegerField | — |
| generated_at | DateTimeField | — |
| generated_by | ForeignKey | auth_user |
| finalized_at | DateTimeField (nullable) | — |
| finalized_by | ForeignKey (nullable) | auth_user |

Constraints: Field-level uniqueness and validation as declared in the model.

## forecast_result

Demand calculation and immutable evidence.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| forecast_run | ForeignKey | forecast_run |
| program_subject | ForeignKey | program_subject |
| source_enrollment | PositiveIntegerField | — |
| failure_adjustment | DecimalField | — |
| forecasted_students | PositiveIntegerField | — |
| required_sections | PositiveIntegerField | — |
| forecast_method | CharField | — |
| computation | JSONField | — |

Constraints: <UniqueConstraint: fields=('forecast_run', 'program_subject') name='unique_forecast_result'>

## course_offering

One section/component requirement.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| forecast_result | ForeignKey | forecast_result |
| program_subject | ForeignKey | program_subject |
| section_number | PositiveIntegerField | — |
| expected_students | PositiveIntegerField | — |
| component_type | CharField | LECTURE, LAB |
| duration_periods | PositiveSmallIntegerField | — |
| meetings_per_week | PositiveSmallIntegerField | — |

Constraints: <UniqueConstraint: fields=('forecast_result', 'section_number', 'component_type') name='unique_offering'>

## course_offering_block

Attendance links.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| course_offering | ForeignKey | course_offering |
| block_section | ForeignKey | block_section |

Constraints: <UniqueConstraint: fields=('course_offering', 'block_section') name='unique_offering_block'>

## schedule_run

Solver execution and saved input snapshot.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| academic_year | CharField | — |
| solver_name | CharField | — |
| status | CharField | — |
| objective_value | FloatField (nullable) | — |
| best_bound | FloatField (nullable) | — |
| mip_gap | FloatField (nullable) | — |
| nodes_explored | PositiveIntegerField (nullable) | — |
| started_at | DateTimeField | — |
| finished_at | DateTimeField (nullable) | — |
| elapsed_seconds | FloatField (nullable) | — |
| scenario_snapshot | JSONField | — |
| diagnostic | TextField | — |

Constraints: Field-level uniqueness and validation as declared in the model.

## schedule_assignment

A persisted meeting start and assigned resources.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| schedule_run | ForeignKey | schedule_run |
| course_offering | ForeignKey | course_offering |
| faculty | ForeignKey | faculty |
| room | ForeignKey | room |
| meeting_number | PositiveSmallIntegerField | — |
| day_index | PositiveSmallIntegerField | — |
| start_period | PositiveSmallIntegerField | — |
| duration_periods | PositiveSmallIntegerField | — |

Constraints: <UniqueConstraint: fields=('schedule_run', 'course_offering', 'meeting_number') name='unique_assignment'>

## solver_metric

Real terminal metric sample.

| Field | Type | Relationship / choices |
|---|---|---|
| id | BigAutoField | — |
| schedule_run | ForeignKey | schedule_run |
| sequence_number | PositiveIntegerField | — |
| elapsed_seconds | FloatField | — |
| objective_value | FloatField (nullable) | — |
| best_bound | FloatField (nullable) | — |
| mip_gap | FloatField (nullable) | — |
| nodes_explored | PositiveIntegerField (nullable) | — |

Constraints: <UniqueConstraint: fields=('schedule_run', 'sequence_number') name='unique_metric'>

## django_migrations

Django schema-migration ledger with id, app, name and applied timestamp. It records only the new project’s applied migrations, plus Django framework migrations.
