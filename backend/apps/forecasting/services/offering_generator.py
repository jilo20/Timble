from django.db import transaction
from django.utils import timezone

from apps.forecasting.models import CourseOffering, CourseOfferingBlock, ForecastRun
from apps.master_data.models import BlockSection


@transaction.atomic
def finalize_forecast(run_id, user):
    run = ForecastRun.objects.select_for_update().get(pk=run_id)
    if run.status == "FINALIZED":
        return run
    if not run.results.exists():
        raise ValueError("Cannot finalize an empty forecast.")
    for result in run.results.select_related(
        "program_subject__program", "program_subject__subject"
    ):
        ps = result.program_subject
        if not ps.is_active or not ps.program.is_active or not ps.subject.is_active:
            raise ValueError("Forecast contains inactive curriculum data; regenerate it.")
        remaining = result.forecasted_students
        blocks = list(
            BlockSection.objects.filter(
                program=ps.program, year_level=ps.year_level, is_active=True
            ).order_by("section_code")
        )
        # Section numbers follow stable alphabetic block order; every section needs a real block.
        if remaining and len(blocks) < result.required_sections:
            raise ValueError(
                f"{ps.program.program_code} year {ps.year_level}: needs {result.required_sections} active blocks. Create/verify blocks first."
            )
        for section in range(1, result.required_sections + 1):
            count = min(run.section_capacity, remaining)
            remaining -= count
            block = blocks[section - 1]
            for component in ["LECTURE", "LAB"]:
                prefix = component.lower()
                config = result.computation["components"][prefix]
                duration = config["duration"]
                meetings = config["meetings"]
                if not duration:
                    continue
                offering = CourseOffering.objects.create(
                    forecast_result=result,
                    program_subject=ps,
                    section_number=section,
                    expected_students=count,
                    component_type=component,
                    duration_periods=duration,
                    meetings_per_week=meetings,
                )
                CourseOfferingBlock.objects.create(course_offering=offering, block_section=block)
    run.status = "FINALIZED"
    run.finalized_at = timezone.now()
    run.finalized_by = user
    run.save()
    return run
