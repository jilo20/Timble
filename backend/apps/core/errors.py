from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"errors": getattr(exc, "message_dict", exc.messages)}, status=400)
    if isinstance(exc, ProtectedError):
        return Response(
            {"errors": "This record is referenced by another record. Deactivate it instead."},
            status=409,
        )
    if isinstance(exc, ValueError):
        return Response({"errors": str(exc)}, status=400)
    return drf_handler(exc, context)
