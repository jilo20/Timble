from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.forecasting.models import ForecastRun
from apps.master_data.api.views import serializer_for
from apps.scheduling.domain.parameters import parameters
from apps.scheduling.domain.results import explanation, inspect_result
from apps.scheduling.domain.scenario import SchedulingScenario
from apps.scheduling.models import ScheduleRun, SolverMetric
from apps.scheduling.services.schedule_service import create_run, launch


@api_view(["GET", "POST"])
def schedules(request):
    if request.method == "POST":

        class Request(serializers.Serializer):
            forecast_id = serializers.PrimaryKeyRelatedField(queryset=ForecastRun.objects.all())

        payload = Request(data=request.data)
        payload.is_valid(raise_exception=True)
        run = create_run(payload.validated_data["forecast_id"].pk)
        launch(run)
        return Response(serializer_for(ScheduleRun)(run).data, status=202)
    return Response(
        [
            {
                k: v
                for k, v in serializer_for(ScheduleRun)(run).data.items()
                if k != "scenario_snapshot"
            }
            for run in ScheduleRun.objects.order_by("-pk")
        ]
    )


@api_view(["GET"])
def schedule_detail(request, pk):
    run = get_object_or_404(ScheduleRun, pk=pk)
    scenario = SchedulingScenario.from_dict(run.scenario_snapshot)
    maps = {
        kind: {row["id"]: row["index"] for row in getattr(scenario, kind)}
        for kind in ["offerings", "faculty", "rooms"]
    }
    assignments = [
        {
            "id": a.pk,
            "offering": maps["offerings"][a.course_offering_id],
            "meeting": a.meeting_number,
            "faculty": maps["faculty"][a.faculty_id],
            "room": maps["rooms"][a.room_id],
            "day": a.day_index,
            "start": a.start_period,
            "duration": a.duration_periods,
        }
        for a in run.assignments.order_by("day_index", "start_period", "pk")
    ]
    data = serializer_for(ScheduleRun)(run).data
    data.update(
        assignments=assignments,
        parameters=parameters(scenario),
        validation=inspect_result(scenario, assignments),
        metrics=serializer_for(SolverMetric)(run.metrics.all(), many=True).data,
        explanations=[explanation(scenario, a) for a in assignments],
    )
    return Response(data)
