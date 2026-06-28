from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.operations.views import (
    DriverAssignmentViewSet,
    DriverViewSet,
    GPSPositionViewSet,
    MaintenanceViewSet,
    RouteCoordinateViewSet,
    ScheduleViewSet,
    TripViewSet,
)

router = DefaultRouter()
router.register(r"drivers", DriverViewSet)
router.register(r"driver-assignments", DriverAssignmentViewSet)
router.register(r"schedules", ScheduleViewSet)
router.register(r"route-coordinates", RouteCoordinateViewSet)
router.register(r"maintenances", MaintenanceViewSet)
router.register(r"trips", TripViewSet)
router.register(r"gps-positions", GPSPositionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
