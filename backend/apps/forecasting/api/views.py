from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.forecasting.models import CourseOffering, CourseOfferingBlock, ForecastRun
from apps.forecasting.services.forecast_engine import generate_forecast
from apps.forecasting.services.offering_generator import finalize_forecast
from apps.master_data.api.views import serializer_for
from apps.master_data.models import BlockSection, Program


@api_view(["GET", "POST"])
def forecasts(request):
    if request.method == "POST":

        class Request(serializers.Serializer):
            academic_year = serializers.CharField()
            section_capacity = serializers.IntegerField(min_value=1, max_value=10000)
            failure_rate = serializers.DecimalField(
                max_digits=7, decimal_places=6, min_value=0, max_value=1
            )
            program_ids = serializers.PrimaryKeyRelatedField(
                queryset=Program.objects.filter(is_active=True),
                many=True,
                required=False,
            )

        payload = Request(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        run = generate_forecast(
            values["academic_year"],
            values["section_capacity"],
            request.user,
            [p.pk for p in values.get("program_ids", [])],
            values["failure_rate"],
        )
        return Response(serializer_for(ForecastRun)(run).data, status=201)
    return Response(
        serializer_for(ForecastRun)(ForecastRun.objects.order_by("-pk"), many=True).data
    )


@api_view(["GET", "POST"])
def forecast_detail(request, pk):
    run = get_object_or_404(ForecastRun, pk=pk)
    if request.method == "POST":
        run = finalize_forecast(pk, request.user)
    data = serializer_for(ForecastRun)(run).data
    results = []
    shared = defaultdict(int)
    for r in run.results.select_related("program_subject__subject", "program_subject__program"):
        item = serializer_for(type(r))(r).data
        item["program"] = r.program_subject.program.program_code
        item["subject"] = r.program_subject.subject.subject_code
        shared[item["subject"]] += r.forecasted_students
        results.append(item)
    data.update(
        results=results,
        shared_subject_totals=dict(shared),
        offerings=serializer_for(CourseOffering)(
            CourseOffering.objects.filter(forecast_result__forecast_run=run), many=True
        ).data,
    )
    return Response(data)


@api_view(["GET", "PUT"])
def offering_blocks(request, pk):
    from django.db import transaction

    offering = get_object_or_404(CourseOffering, pk=pk)
    if request.method == "PUT":

        class BlockRequest(serializers.Serializer):
            block_ids = serializers.ListField(
                child=serializers.IntegerField(min_value=1), allow_empty=False
            )

        payload = BlockRequest(data=request.data)
        payload.is_valid(raise_exception=True)
        ids = payload.validated_data["block_ids"]
        if len(ids) != len(set(ids)):
            raise ValueError("Select distinct blocks.")
        blocks = list(
            BlockSection.objects.filter(pk__in=ids, is_active=True, program__is_active=True)
        )
        if len(blocks) != len(ids):
            raise ValueError("Unknown or inactive block.")
        with transaction.atomic():
            offering.block_links.all().delete()
            for block in blocks:
                CourseOfferingBlock.objects.create(course_offering=offering, block_section=block)
    return Response(
        {"block_ids": list(offering.block_links.values_list("block_section_id", flat=True))}
    )
