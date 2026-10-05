from apps.bulk_import.api import bulk, bundle
from apps.core.auth import session
from apps.forecasting.api.views import forecast_detail, forecasts, offering_blocks
from apps.master_data.api.registry import RESOURCES
from apps.master_data.api.views import schema, viewset_for
from apps.scheduling.api.views import schedule_detail, schedules
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
for name, model in RESOURCES.items():
    router.register(name, viewset_for(model), basename=name)
urlpatterns = [
    path("api/session/", session),
    path("api/schema/", schema),
    path("api/bulk/<str:kind>/", bulk),
    path("api/bulk-bundle/", bundle),
    path("api/forecasts/", forecasts),
    path("api/forecasts/<int:pk>/", forecast_detail),
    path("api/offerings/<int:pk>/blocks/", offering_blocks),
    path("api/schedules/", schedules),
    path("api/schedules/<int:pk>/", schedule_detail),
    path("api/", include(router.urls)),
]
