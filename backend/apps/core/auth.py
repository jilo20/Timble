import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


@ensure_csrf_cookie
@csrf_protect
@require_http_methods(["GET", "POST", "DELETE"])
def session(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"errors": "Invalid JSON"}, status=400)
        user = authenticate(request, username=data.get("username"), password=data.get("password"))
        if user is None:
            return JsonResponse({"errors": "Invalid username or password."}, status=403)
        login(request, user)
    if request.method == "DELETE":
        logout(request)
    return JsonResponse(
        {
            "authenticated": request.user.is_authenticated,
            "username": request.user.get_username(),
        }
    )
