import os
import subprocess
import sys

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.scheduling.domain.results import inspect_result
from apps.scheduling.domain.scenario import SchedulingScenario
from apps.scheduling.models import ScheduleAssignment, ScheduleRun, SolverMetric
from apps.scheduling.optimization.solver import solve

from .scenario_builder import build_scenario


def create_run(forecast_id):
    from apps.forecasting.models import ForecastRun

    scenario = build_scenario(forecast_id)
    forecast = ForecastRun.objects.get(pk=forecast_id)
    return ScheduleRun.objects.create(
        academic_year=forecast.academic_year, scenario_snapshot=scenario.to_dict()
    )


def launch(run):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        subprocess.Popen(
            [
                sys.executable,
                str(settings.BASE_DIR / "manage.py"),
                "solve_run",
                str(run.pk),
            ],
            cwd=settings.BASE_DIR,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        run.status = "ERROR"
        run.diagnostic = str(exc)
        run.finished_at = timezone.now()
        run.save()
        raise ValueError("Unable to start the solver worker.")


def execute_run(run_id):
    if not ScheduleRun.objects.filter(pk=run_id, status="QUEUED").update(status="RUNNING"):
        return
    run = ScheduleRun.objects.get(pk=run_id)
    try:
        scenario = SchedulingScenario.from_dict(run.scenario_snapshot)
        result = solve(scenario)
        if result["assignments"]:
            validation = inspect_result(scenario, result["assignments"])
            if not validation["valid"]:
                raise ValueError(str(validation["violations"]))
        with transaction.atomic():
            for a in result.pop("assignments"):
                ScheduleAssignment.objects.create(
                    schedule_run=run,
                    course_offering_id=scenario.offerings[a["offering"] - 1]["id"],
                    faculty_id=scenario.faculty[a["faculty"] - 1]["id"],
                    room_id=scenario.rooms[a["room"] - 1]["id"],
                    meeting_number=a["meeting"],
                    day_index=a["day"],
                    start_period=a["start"],
                    duration_periods=a["duration"],
                )
            for key, value in result.items():
                setattr(run, key, value)
            run.finished_at = timezone.now()
            run.save()
            SolverMetric.objects.create(
                schedule_run=run,
                sequence_number=1,
                **{
                    k: result[k]
                    for k in [
                        "elapsed_seconds",
                        "objective_value",
                        "best_bound",
                        "mip_gap",
                        "nodes_explored",
                    ]
                },
            )
    except Exception as exc:
        run.status = "ERROR"
        run.diagnostic = str(exc)
        run.finished_at = timezone.now()
        run.elapsed_seconds = (run.finished_at - run.started_at).total_seconds()
        run.save()
    return run
