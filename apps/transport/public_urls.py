from django.urls import path

from apps.transport.public_views import (
    PublicBusStopList,
    PublicRouteCoordinates,
    PublicRouteList,
    PublicRouteStops,
)

urlpatterns = [
    path("routes/", PublicRouteList.as_view(), name="public-routes"),
    path("routes/<int:pk>/stops/", PublicRouteStops.as_view(), name="public-route-stops"),
    path("routes/<int:pk>/coordinates/", PublicRouteCoordinates.as_view(), name="public-route-coordinates"),
    path("bus-stops/", PublicBusStopList.as_view(), name="public-bus-stops"),
]
