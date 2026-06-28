import django_filters
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadOnlyOrAdminWrite
from apps.incidents.models import Incident, IncidentType
from apps.incidents.serializers import (
    IncidentListSerializer,
    IncidentSerializer,
    IncidentTypeSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Listar tipos de incidente", description="Obtener listado de tipos de incidente disponibles (accidente, falla mecánica, retraso, etc.).", tags=["Incidents"]),
    create=extend_schema(summary="Crear tipo de incidente", description="Registrar un nuevo tipo de incidente.", tags=["Incidents"]),
    retrieve=extend_schema(summary="Obtener tipo de incidente", description="Obtener detalle de un tipo de incidente por su ID.", tags=["Incidents"]),
    update=extend_schema(summary="Actualizar tipo de incidente", description="Reemplazar todos los datos de un tipo de incidente.", tags=["Incidents"]),
    partial_update=extend_schema(summary="Actualizar parcialmente tipo de incidente", description="Actualizar campos específicos.", tags=["Incidents"]),
    destroy=extend_schema(summary="Eliminar tipo de incidente", description="Eliminar (soft delete) un tipo de incidente.", tags=["Incidents"]),
)
class IncidentTypeViewSet(ModelViewSet):
    queryset = IncidentType.objects.all()
    serializer_class = IncidentTypeSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


class IncidentFilter(django_filters.FilterSet):
    created_at_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Incident
        fields = ["trip", "incident_type", "vehicle", "driver", "severity", "status",
                   "created_at_after", "created_at_before"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar incidentes",
        description="Obtener listado paginado de incidentes. Filtrable por viaje, tipo, vehículo, conductor, severidad, estado y rango de fechas. La lista incluye nombre del tipo de incidente e información del viaje.",
        tags=["Incidents"],
        parameters=[
            OpenApiParameter(name="trip", type=int, description="ID del viaje"),
            OpenApiParameter(name="incident_type", type=int, description="ID del tipo de incidente"),
            OpenApiParameter(name="vehicle", type=int, description="ID del vehículo"),
            OpenApiParameter(name="severity", type=str, description="Severidad (low/medium/high)"),
            OpenApiParameter(name="status", type=str, description="Estado (open/in_progress/resolved)"),
            OpenApiParameter(name="created_at_after", type=str, description="Desde fecha/hora (ISO 8601)"),
            OpenApiParameter(name="created_at_before", type=str, description="Hasta fecha/hora (ISO 8601)"),
        ],
        examples=[
            OpenApiExample(
                name="Lista de incidentes abiertos",
                value=[
                    {"id": 1, "trip": 2, "trip_info": "RT-ECO ECO-001 2026-06-28", "incident_type": 2, "incident_type_name": "Accidente", "description": "Freno de emergencia por obstáculo en la vía", "severity": "low", "status": "open"},
                ],
                response_only=True,
            ),
        ],
    ),
    create=extend_schema(
        summary="Reportar incidente",
        description="Registrar un nuevo incidente. Dispara una notificación automática a todos los administradores. Incluye coordenadas, severidad y tipo.",
        tags=["Incidents"],
        examples=[
            OpenApiExample(
                name="Reportar incidente",
                value={
                    "trip": 2, "incident_type": 2, "vehicle": 2, "driver": 2,
                    "latitude": -0.1674, "longitude": -78.4759,
                    "description": "Freno de emergencia por obstáculo en la vía",
                    "severity": "medium",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(summary="Obtener incidente", description="Obtener detalle de un incidente por su ID.", tags=["Incidents"]),
    update=extend_schema(summary="Actualizar incidente", description="Reemplazar todos los datos de un incidente.", tags=["Incidents"]),
    partial_update=extend_schema(summary="Actualizar parcialmente incidente", description="Actualizar campos específicos de un incidente (severidad, descripción, etc.).", tags=["Incidents"]),
    destroy=extend_schema(summary="Eliminar incidente", description="Eliminar (soft delete) un incidente.", tags=["Incidents"]),
)
class IncidentViewSet(ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = IncidentFilter
    search_fields = ["description", "trip__route__code", "incident_type__name"]
    ordering_fields = ["created_at", "severity", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return IncidentListSerializer
        return IncidentSerializer

    @extend_schema(
        summary="Resolver incidente",
        description="Marca un incidente como resuelto, estableciendo la fecha/hora actual como resolved_at.",
        tags=["Incidents"],
        responses={200: IncidentSerializer},
        examples=[
            OpenApiExample(
                name="Resolver incidente",
                value={"status": "resolved", "resolved_at": "2026-06-28T09:00:00Z"},
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["patch"])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        incident.status = Incident.Status.RESOLVED
        incident.resolved_at = now()
        incident.save()
        return Response(IncidentSerializer(incident).data)
