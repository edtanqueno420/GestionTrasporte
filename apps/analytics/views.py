from datetime import date

from django.db.models import Avg, F
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.incidents.models import Incident
from apps.operations.models import Maintenance, RouteCoordinate, Trip
from apps.transport.models import Route, Vehicle


class DashboardView(APIView):
    @extend_schema(
        summary="Dashboard — KPIs generales",
        description="Obtener indicadores clave del sistema: viajes hoy, vehículos activos, incidentes abiertos, duración promedio de viajes y tasa de puntualidad.",
        tags=["Analytics"],
        responses={
            200: OpenApiResponse(
                description="Dashboard KPIs",
                response={
                    "type": "object",
                    "properties": {
                        "total_trips_today": {"type": "integer", "example": 1},
                        "active_vehicles": {"type": "integer", "example": 2},
                        "total_incidents_open": {"type": "integer", "example": 1},
                        "average_trip_duration_minutes": {"type": "number", "example": 120.0},
                        "punctuality_rate": {"type": "number", "example": 0.0},
                    },
                },
            ),
        },
        examples=[
            OpenApiExample(
                name="Respuesta del dashboard",
                value={
                    "total_trips_today": 1,
                    "active_vehicles": 2,
                    "total_incidents_open": 1,
                    "average_trip_duration_minutes": 120.0,
                    "punctuality_rate": 0.0,
                },
                response_only=True,
            ),
        ],
    )
    def get(self, request):
        today = date.today()
        trips_today = Trip.objects.filter(
            trip_date=today, is_active=True,
        ).count()
        active_vehicles = Vehicle.objects.filter(is_active=True).count()
        incidents_open = Incident.objects.filter(
            is_active=True, status=Incident.Status.OPEN,
        ).count()
        avg_duration = Trip.objects.filter(
            is_active=True,
            arrival_datetime__isnull=False,
            departure_datetime__isnull=False,
        ).annotate(
            duration=F("arrival_datetime") - F("departure_datetime"),
        ).aggregate(avg=Avg("duration"))
        avg_seconds = avg_duration["avg"].total_seconds() if avg_duration["avg"] else 0
        avg_minutes = round(avg_seconds / 60, 1) if avg_seconds else 0

        total_completed = Trip.objects.filter(
            is_active=True, status=Trip.Status.COMPLETED,
        ).count()
        total_cancelled = Trip.objects.filter(
            is_active=True, status=Trip.Status.CANCELLED,
        ).count()
        total_scheduled = Trip.objects.filter(is_active=True).count()
        punctuality_rate = 0
        if total_scheduled > 0:
            punctuality_rate = round(
                (total_completed / (total_scheduled - total_cancelled)) * 100
                if (total_scheduled - total_cancelled) > 0 else 0, 1,
            )

        return Response({
            "total_trips_today": trips_today,
            "active_vehicles": active_vehicles,
            "total_incidents_open": incidents_open,
            "average_trip_duration_minutes": avg_minutes,
            "punctuality_rate": punctuality_rate,
        })


class RouteReportView(APIView):
    @extend_schema(
        summary="Reporte de ruta",
        description="Obtener métricas detalladas de una ruta: total de viajes, duración promedio, conteo de incidentes y score de rendimiento.",
        tags=["Analytics"],
        parameters=[
            OpenApiParameter(name="pk", location="path", required=True, type=int, description="ID de la ruta"),
        ],
        responses={
            200: OpenApiResponse(
                description="Reporte de ruta",
                response={
                    "type": "object",
                    "properties": {
                        "route_id": {"type": "integer"},
                        "route_code": {"type": "string"},
                        "route_name": {"type": "string"},
                        "total_trips": {"type": "integer"},
                        "average_duration_minutes": {"type": "number"},
                        "incident_count": {"type": "integer"},
                        "performance_score": {"type": "number"},
                    },
                },
            ),
            404: OpenApiResponse(description="Ruta no encontrada"),
        },
    )
    def get(self, request, pk):
        try:
            route = Route.objects.get(pk=pk, is_active=True)
        except Route.DoesNotExist:
            return Response(
                {"error": "Ruta no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )
        trips_qs = Trip.objects.filter(route=route, is_active=True)
        total_trips = trips_qs.count()

        avg_duration = trips_qs.filter(
            arrival_datetime__isnull=False,
            departure_datetime__isnull=False,
        ).annotate(
            duration=F("arrival_datetime") - F("departure_datetime"),
        ).aggregate(avg=Avg("duration"))
        avg_seconds = avg_duration["avg"].total_seconds() if avg_duration["avg"] else 0
        avg_minutes = round(avg_seconds / 60, 1) if avg_seconds else 0

        incident_count = Incident.objects.filter(
            trip__route=route, is_active=True,
        ).count()

        total_scheduled = trips_qs.count()
        completed = trips_qs.filter(status=Trip.Status.COMPLETED).count()
        completed_ratio = completed / total_scheduled if total_scheduled > 0 else 0
        performance_score = round(
            (completed_ratio * 100) - (incident_count * 5), 1,
        )
        performance_score = max(0, performance_score)

        return Response({
            "route_id": route.id,
            "route_code": route.code,
            "route_name": route.name,
            "total_trips": total_trips,
            "average_duration_minutes": avg_minutes,
            "incident_count": incident_count,
            "performance_score": performance_score,
        })


class VehicleReportView(APIView):
    @extend_schema(
        summary="Reporte de vehículo",
        description="Obtener métricas de un vehículo: cantidad de viajes, kilometraje estimado, mantenimientos e incidentes vinculados.",
        tags=["Analytics"],
        parameters=[
            OpenApiParameter(name="pk", location="path", required=True, type=int, description="ID del vehículo"),
        ],
        responses={
            200: OpenApiResponse(
                description="Reporte de vehículo",
                response={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "integer"},
                        "vehicle_plate": {"type": "string"},
                        "trips_count": {"type": "integer"},
                        "estimated_km": {"type": "number"},
                        "maintenance_count": {"type": "integer"},
                        "incidents_linked": {"type": "integer"},
                    },
                },
            ),
            404: OpenApiResponse(description="Vehículo no encontrado"),
        },
    )
    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk, is_active=True)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehículo no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        trips_count = Trip.objects.filter(vehicle=vehicle, is_active=True).count()
        coordinate_count = RouteCoordinate.objects.filter(
            route__trips__vehicle=vehicle,
        ).distinct().count()
        estimated_km = round(coordinate_count * 0.5, 2)

        maintenance_count = Maintenance.objects.filter(
            vehicle=vehicle, is_active=True,
        ).count()
        incidents_linked = Incident.objects.filter(
            vehicle=vehicle, is_active=True,
        ).count()

        return Response({
            "vehicle_id": vehicle.id,
            "vehicle_plate": vehicle.plate,
            "trips_count": trips_count,
            "estimated_km": estimated_km,
            "maintenance_count": maintenance_count,
            "incidents_linked": incidents_linked,
        })


class SystemStatusView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Estado del sistema (público)",
        description="Obtener estado general del sistema: rutas activas, vehículos, incidentes abiertos y viajes activos hoy. No requiere autenticación.",
        tags=["Analytics"],
        responses={
            200: OpenApiResponse(
                description="Estado del sistema",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "operational"},
                        "active_routes": {"type": "integer"},
                        "active_vehicles": {"type": "integer"},
                        "open_incidents": {"type": "integer"},
                        "active_trips_today": {"type": "integer"},
                    },
                },
            ),
        },
        examples=[
            OpenApiExample(
                name="Sistema operativo",
                value={"status": "operational", "active_routes": 4, "active_vehicles": 2, "open_incidents": 1, "active_trips_today": 1},
                response_only=True,
            ),
        ],
    )
    def get(self, request):
        active_routes = Route.objects.filter(is_active=True).count()
        active_vehicles = Vehicle.objects.filter(is_active=True).count()
        incidents_open = Incident.objects.filter(
            is_active=True, status=Incident.Status.OPEN,
        ).count()
        active_trips_today = Trip.objects.filter(
            trip_date=date.today(), is_active=True,
            status__in=[Trip.Status.IN_PROGRESS, Trip.Status.SCHEDULED],
        ).count()

        return Response({
            "status": "operational",
            "active_routes": active_routes,
            "active_vehicles": active_vehicles,
            "open_incidents": incidents_open,
            "active_trips_today": active_trips_today,
        })
