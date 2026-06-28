from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.transport.views import (
    BusStopViewSet,
    DistrictViewSet,
    RouteBusStopViewSet,
    RouteViewSet,
    SectorViewSet,
    TransportCompanyViewSet,
    VehicleStatusViewSet,
    VehicleTypeViewSet,
    VehicleViewSet,
)

router = DefaultRouter()
router.register(r"routes", RouteViewSet)
router.register(r"bus-stops", BusStopViewSet)
router.register(r"vehicles", VehicleViewSet)
router.register(r"transport-companies", TransportCompanyViewSet)
router.register(r"districts", DistrictViewSet)
router.register(r"sectors", SectorViewSet)
router.register(r"vehicle-types", VehicleTypeViewSet)
router.register(r"vehicle-statuses", VehicleStatusViewSet)
router.register(r"route-bus-stops", RouteBusStopViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
