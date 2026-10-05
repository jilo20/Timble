from decimal import ROUND_CEILING, Decimal, InvalidOperation
from math import ceil

from django.db import transaction

from apps.core.validation import academic_year
from apps.forecasting.models import ForecastResult, ForecastRun, HistoricalEnrollment
from apps.master_data.models import ProgramSubject


def computation(ps, year, capacity, failure_rate):
    prior = f"{int(year[:4]) - 1}-{int(year[:4])}"
    prerequisites = [
        p.prerequisite_program_subject
        for p in ps.prerequisites.select_related("prerequisite_program_subject__subject")
    ]
    evidence = []
    for source in prerequisites or [ps]:
        if not source.is_active or not source.subject.is_active:
            raise ValueError(f"Inactive prerequisite for {ps.subject.subject_code}.")
        history = HistoricalEnrollment.objects.filter(
            academic_year=prior, program=ps.program, subject=source.subject
        ).first()
        if history is None:
            raise ValueError(
                f"Missing {prior} history: {ps.program.program_code} / {source.subject.subject_code}."
            )
        rate = failure_rate if prerequisites else Decimal(0)
        adjusted = Decimal(history.enrollment_count) * (1 - rate)
        evidence.append(
            {
                "subject": source.subject.subject_code,
                "source": history.enrollment_count,
                "rate": str(rate),
                "adjusted": str(adjusted),
                "history_id": history.pk,
            }
        )
    chosen = max(evidence, key=lambda row: Decimal(row["adjusted"]))
    students = int(Decimal(chosen["adjusted"]).to_integral_value(rounding=ROUND_CEILING))
    return {
        "source_enrollment": chosen["source"],
        "failure_adjustment": Decimal(chosen["source"]) - Decimal(chosen["adjusted"]),
        "forecasted_students": students,
        "required_sections": ceil(students / capacity),
        "forecast_method": "PREREQUISITE_MAX" if prerequisites else "OWN_PRIOR_ENROLLMENT",
        "computation": {
            "components": {
                kind: {
                    "duration": getattr(ps, kind + "_periods"),
                    "meetings": getattr(ps, kind + "_meetings_per_week"),
                    "room_type": getattr(ps, kind + "_room_type"),
                }
                for kind in ["lecture", "lab"]
            },
            "historical_year": prior,
            "program": ps.program.program_code,
            "subject": ps.subject.subject_code,
            "evidence": evidence,
            "selected_source": chosen["subject"],
            "section_capacity": capacity,
            "rounding": "CEILING after MAX",
            "formula": "ceil(MAX(H * (1 - rate)))"
            if prerequisites
            else "own previous-year enrollment",
        },
    }


@transaction.atomic
def generate_forecast(year, capacity, user, program_ids=None, failure_rate=None):
    academic_year(year)
    try:
        failure_rate = Decimal(str(failure_rate))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Enter a forecast failure-rate assumption between 0 and 1.")
    if not failure_rate.is_finite() or not 0 <= failure_rate <= 1:
        raise ValueError("Failure rate must be between 0 and 1.")
    if failure_rate.as_tuple().exponent < -6:
        raise ValueError("Failure rate supports at most six decimal places.")
    capacity = int(capacity)
    if capacity < 1 or capacity > 10000:
        raise ValueError("Section capacity must be 1–10000.")
    subjects = (
        ProgramSubject.objects.filter(
            is_active=True, program__is_active=True, subject__is_active=True
        )
        .select_related("program", "subject")
        .order_by("pk")
    )
    if program_ids:
        subjects = subjects.filter(program_id__in=program_ids)
    if not subjects.exists():
        raise ValueError("No active curriculum subjects in the selected scope.")
    run = ForecastRun.objects.create(
        academic_year=year, section_capacity=capacity, generated_by=user
    )
    for ps in subjects:
        ForecastResult.objects.create(
            forecast_run=run,
            program_subject=ps,
            **computation(ps, year, capacity, failure_rate),
        )
    return run
