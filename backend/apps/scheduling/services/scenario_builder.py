from apps.forecasting.models import CourseOffering, ForecastRun
from apps.master_data.models import BlockSection, Faculty, FacultyTeachingRule, Room
from apps.scheduling.domain.scenario import DAYS, PERIODS, SchedulingScenario


def build_scenario(forecast_id):
    run = ForecastRun.objects.get(pk=forecast_id)
    if run.status != "FINALIZED":
        raise ValueError("Finalize the forecast before scheduling.")
    source = list(
        CourseOffering.objects.filter(forecast_result__forecast_run=run)
        .select_related("program_subject__subject", "program_subject__program", "forecast_result")
        .prefetch_related("block_links__block_section")
        .order_by("pk")
    )
    if not source:
        raise ValueError("No offerings to schedule.")
    faculty = [
        {
            "index": i,
            "id": f.pk,
            "label": f"{f.employee_code} Â· {f.first_name} {f.last_name}",
            "max_load": f.max_teaching_load,
        }
        for i, f in enumerate(Faculty.objects.filter(is_active=True).order_by("pk"), 1)
    ]
    rooms = [
        {
            "index": i,
            "id": r.pk,
            "label": r.room_code,
            "type": r.room_type,
            "capacity": r.capacity,
        }
        for i, r in enumerate(Room.objects.filter(is_active=True).order_by("pk"), 1)
    ]
    block_ids = {link.block_section_id for o in source for link in o.block_links.all()}
    blocks = [
        {
            "index": i,
            "id": b.pk,
            "label": f"{b.program.program_code}-{b.year_level}{b.section_code}",
        }
        for i, b in enumerate(
            BlockSection.objects.filter(pk__in=block_ids, is_active=True, program__is_active=True)
            .select_related("program")
            .order_by("pk"),
            1,
        )
    ]
    bmap = {b["id"]: b["index"] for b in blocks}
    subjects = sorted(
        {(o.program_subject.subject_id, o.program_subject.subject.subject_code) for o in source}
    )
    subjects = [
        {"index": i, "id": sid, "label": label} for i, (sid, label) in enumerate(subjects, 1)
    ]
    smap = {s["id"]: s["index"] for s in subjects}
    offerings = []
    for i, o in enumerate(source, 1):
        ps = o.program_subject
        if not ps.is_active or not ps.program.is_active or not ps.subject.is_active:
            raise ValueError("Inactive curriculum data in offerings; create a new forecast.")
        links = list(o.block_links.all())
        if not links or any(link.block_section_id not in bmap for link in links):
            raise ValueError(f"Offering {o.pk} needs active student blocks.")
        offerings.append(
            {
                "index": i,
                "id": o.pk,
                "subject": smap[ps.subject_id],
                "label": f"{ps.subject.subject_code} Â· {ps.program.program_code} Â· {o.section_number} Â· {o.component_type}",
                "students": o.expected_students,
                "duration": o.duration_periods,
                "meetings": o.meetings_per_week,
                "room_type": o.forecast_result.computation["components"][o.component_type.lower()][
                    "room_type"
                ],
                "blocks": [bmap[link.block_section_id] for link in links],
            }
        )
    fmap = {f["id"]: f["index"] for f in faculty}
    rules = [
        {
            "faculty": fmap[r.faculty_id],
            "subject": smap[r.subject_id],
            "rule": r.teaching_rule,
        }
        for r in FacultyTeachingRule.objects.filter(faculty_id__in=fmap, subject_id__in=smap)
    ]
    if not faculty or not rooms:
        raise ValueError("Active faculty and rooms are required.")
    return SchedulingScenario(offerings, faculty, rooms, blocks, subjects, rules, DAYS, PERIODS)
