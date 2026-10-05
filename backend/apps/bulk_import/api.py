from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .schema import FILES, SCHEMAS
from .services.importer import import_csv


@api_view(["GET", "POST"])
def bulk(request, kind):
    if kind not in SCHEMAS:
        return Response({"errors": "Unknown import type"}, status=404)
    if request.method == "GET":
        response = HttpResponse(SCHEMAS[kind] + "\n", content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{FILES.get(kind, kind)}.csv"'
        return response
    uploaded = request.FILES.get("file")
    if not uploaded:
        raise ValueError("Select a UTF-8 CSV file.")
    if uploaded.size > 10 * 1024 * 1024:
        raise ValueError("Maximum file size is 10 MB.")
    try:
        result = import_csv(kind, uploaded.read(), request.data.get("commit") == "true")
    except UnicodeDecodeError:
        raise ValueError("The file must be UTF-8 CSV.")
    return Response(result, status=200 if result["valid"] else 400)


@api_view(["GET", "POST"])
def bundle(request):
    from .services.bundle import MAX_ARCHIVE_BYTES, import_bundle, package_bytes

    if request.method == "GET":
        package = request.query_params.get("package", "templates")
        content = package_bytes(package)
        names = {
            "templates": "timble-templates.zip",
            "datasets": "datasets.zip",
            "demo": "demo-datasets.zip",
        }
        response = HttpResponse(content, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{names[package]}"'
        return response
    uploaded = request.FILES.get("file")
    if not uploaded:
        raise ValueError("Select the dataset ZIP package.")
    if uploaded.size > MAX_ARCHIVE_BYTES:
        raise ValueError("Maximum ZIP upload size is 10 MB.")
    result = import_bundle(uploaded.read(), request.data.get("commit") == "true")
    return Response(result, status=200 if result["valid"] else 400)
