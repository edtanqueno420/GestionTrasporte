from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.incidents.views import IncidentTypeViewSet, IncidentViewSet

router = DefaultRouter()
router.register(r"incident-types", IncidentTypeViewSet)
router.register(r"incidents", IncidentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
