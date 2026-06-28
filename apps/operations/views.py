import django_filters
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadOnlyOrAdminWrite
from apps.operations.models import (
    Driver,
    DriverAssignment,
    GPSPosition,
    Maintenance,
    RouteCoordinate,
    Schedule,
    Trip,
)
from apps.operations.serializers import (
    DriverAssignmentSerializer,
    DriverSerializer,
    GPSPositionSerializer,
    MaintenanceSerializer,
    RouteCoordinateSerializer,
    ScheduleSerializer,
    TripSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Listar conductores", description="Obtener listado paginado de conductores. Filtrable por tipo de licencia y disponibilidad. Búsqueda por nombre de usuario, apellido o licencia.", tags=["Operations"]),
    create=extend_schema(summary="Crear conductor", description="Registrar un nuevo conductor asociado a un usuario existente.", tags=["Operations"]),
    retrieve=extend_schema(summary="Obtener conductor", description="Obtener detalle de un conductor por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar conductor", description="Reemplazar todos los datos de un conductor.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente conductor", description="Actualizar campos específicos de un conductor.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar conductor", description="Eliminar (soft delete) un conductor.", tags=["Operations"]),
)
class DriverViewSet(ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["user__username", "user__first_name", "user__last_name", "license_number"]
    filterset_fields = ["license_type", "is_available"]
    ordering_fields = ["user__first_name", "hire_date", "experience_years"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar asignaciones", description="Obtener listado paginado de asignaciones conductor-vehículo. Filtrable por conductor, vehículo y asignación activa.", tags=["Operations"]),
    create=extend_schema(summary="Crear asignación", description="Asignar un conductor a un vehículo. Solo una asignación activa por vehículo.", tags=["Operations"]),
    retrieve=extend_schema(summary="Obtener asignación", description="Obtener detalle de una asignación por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar asignación", description="Reemplazar todos los datos de una asignación.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente asignación", description="Finalizar o modificar una asignación.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar asignación", description="Eliminar (soft delete) una asignación.", tags=["Operations"]),
)
class DriverAssignmentViewSet(ModelViewSet):
    queryset = DriverAssignment.objects.all()
    serializer_class = DriverAssignmentSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["driver", "vehicle", "is_active_assignment"]
    ordering_fields = ["assignment_date", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar horarios", description="Obtener listado paginado de horarios de rutas. Filtrable por ruta y búsqueda por código/nombre de ruta.", tags=["Operations"]),
    create=extend_schema(summary="Crear horario", description="Registrar un horario para una ruta con hora de salida, llegada, frecuencia y días de operación.", tags=["Operations"]),
    retrieve=extend_schema(summary="Obtener horario", description="Obtener detalle de un horario por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar horario", description="Reemplazar todos los datos de un horario.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente horario", description="Actualizar campos específicos de un horario.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar horario", description="Eliminar (soft delete) un horario.", tags=["Operations"]),
)
class ScheduleViewSet(ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["route"]
    search_fields = ["route__code", "route__name"]
    ordering_fields = ["route", "departure_time", "created_at"]
    ordering = ["route", "departure_time"]


@extend_schema_view(
    list=extend_schema(summary="Listar coordenadas de ruta", description="Obtener listado paginado de coordenadas que forman la polyline de una ruta. Filtrable por ruta.", tags=["Operations"]),
    create=extend_schema(summary="Crear coordenada de ruta", description="Agregar un punto coordenado a una ruta con un orden específico.", tags=["Operations"]),
    retrieve=extend_schema(summary="Obtener coordenada", description="Obtener detalle de una coordenada por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar coordenada", description="Reemplazar todos los datos de una coordenada.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente coordenada", description="Actualizar campos específicos de una coordenada.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar coordenada", description="Eliminar (soft delete) una coordenada.", tags=["Operations"]),
)
class RouteCoordinateViewSet(ModelViewSet):
    queryset = RouteCoordinate.objects.all()
    serializer_class = RouteCoordinateSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["route"]
    ordering_fields = ["route", "order"]
    ordering = ["route", "order"]


@extend_schema_view(
    list=extend_schema(summary="Listar mantenimientos", description="Obtener listado paginado de registros de mantenimiento. Filtrable por vehículo, tipo y estado. Búsqueda por placa o descripción.", tags=["Operations"]),
    create=extend_schema(summary="Crear mantenimiento", description="Registrar una orden de mantenimiento para un vehículo.", tags=["Operations"]),
    retrieve=extend_schema(summary="Obtener mantenimiento", description="Obtener detalle de un mantenimiento por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar mantenimiento", description="Reemplazar todos los datos de un mantenimiento.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente mantenimiento", description="Actualizar estado o fechas de un mantenimiento.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar mantenimiento", description="Eliminar (soft delete) un registro de mantenimiento.", tags=["Operations"]),
)
class MaintenanceViewSet(ModelViewSet):
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["vehicle", "maintenance_type", "status"]
    search_fields = ["vehicle__plate", "description"]
    ordering_fields = ["scheduled_date", "cost", "created_at"]
    ordering = ["-scheduled_date", "-created_at"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar viajes",
        description="Obtener listado paginado de viajes. Filtrable por ruta, vehículo, conductor, estado y fecha. Búsqueda por código de ruta, placa, conductor. Incluye reportes de analítica.",
        tags=["Operations"],
        parameters=[
            OpenApiParameter(name="route", type=int, description="ID de la ruta"),
            OpenApiParameter(name="vehicle", type=int, description="ID del vehículo"),
            OpenApiParameter(name="driver", type=int, description="ID del conductor"),
            OpenApiParameter(name="status", type=str, description="Estado del viaje (scheduled/in_progress/completed/cancelled)"),
            OpenApiParameter(name="trip_date", type=str, description="Fecha del viaje (YYYY-MM-DD)"),
            OpenApiParameter(name="search", type=str, description="Búsqueda por código de ruta, placa, conductor u observaciones"),
        ],
    ),
    create=extend_schema(
        summary="Crear viaje",
        description="Registrar un nuevo viaje. Valida que el horario pertenezca a la ruta y que vehículo y ruta sean de la misma empresa.",
        tags=["Operations"],
        examples=[
            OpenApiExample(
                name="Crear viaje en curso",
                value={
                    "route": 5, "vehicle": 2, "driver": 2, "schedule": 1,
                    "trip_date": "2026-06-28",
                    "departure_datetime": "2026-06-28T08:00:00Z",
                    "status": "in_progress", "passenger_count": 85,
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(summary="Obtener viaje", description="Obtener detalle de un viaje por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar viaje", description="Reemplazar todos los datos de un viaje.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente viaje", description="Actualizar campos específicos de un viaje (estado, pasajeros, etc.).", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar viaje", description="Eliminar (soft delete) un viaje.", tags=["Operations"]),
)
class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["route", "vehicle", "driver", "status", "trip_date"]
    search_fields = ["route__code", "vehicle__plate", "driver__user__username", "observations"]
    ordering_fields = ["trip_date", "departure_datetime", "arrival_datetime", "created_at"]
    ordering = ["-trip_date", "-departure_datetime"]


class GPSPositionFilter(django_filters.FilterSet):
    recorded_at_after = django_filters.DateTimeFilter(field_name="recorded_at", lookup_expr="gte")
    recorded_at_before = django_filters.DateTimeFilter(field_name="recorded_at", lookup_expr="lte")

    class Meta:
        model = GPSPosition
        fields = ["trip", "recorded_at_after", "recorded_at_before"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar posiciones GPS",
        description="Obtener posiciones GPS registradas para viajes. Filtrable por viaje y rango de fechas. Útil para tracking en tiempo real y replay de rutas.",
        tags=["Operations"],
        parameters=[
            OpenApiParameter(name="trip", type=int, description="ID del viaje para filtrar posiciones"),
            OpenApiParameter(name="recorded_at_after", type=str, description="Filtrar desde fecha/hora (ISO 8601)"),
            OpenApiParameter(name="recorded_at_before", type=str, description="Filtrar hasta fecha/hora (ISO 8601)"),
        ],
        examples=[
            OpenApiExample(
                name="Posiciones del viaje 2 en los últimos 5 minutos",
                value=[
                    {"id": 1, "trip": 2, "latitude": -0.173175, "longitude": -78.479125, "speed": 25.5, "heading": 180.0, "recorded_at": "2026-06-28T08:05:00Z"},
                    {"id": 2, "trip": 2, "latitude": -0.176950, "longitude": -78.480350, "speed": 18.3, "heading": 190.0, "recorded_at": "2026-06-28T08:07:00Z"},
                ],
                response_only=True,
            ),
        ],
    ),
    create=extend_schema(
        summary="Crear posición GPS",
        description="Registrar una nueva posición GPS para un viaje. Incluye latitud, longitud, velocidad y dirección.",
        tags=["Operations"],
        examples=[
            OpenApiExample(
                name="Registrar posición",
                value={
                    "trip": 2, "latitude": -0.1694, "longitude": -78.4779,
                    "speed": 25.5, "heading": 180.0, "recorded_at": "2026-06-28T08:05:00Z",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(summary="Obtener posición GPS", description="Obtener detalle de una posición GPS por su ID.", tags=["Operations"]),
    update=extend_schema(summary="Actualizar posición GPS", description="Reemplazar todos los datos de una posición GPS.", tags=["Operations"]),
    partial_update=extend_schema(summary="Actualizar parcialmente posición GPS", description="Actualizar campos específicos de una posición GPS.", tags=["Operations"]),
    destroy=extend_schema(summary="Eliminar posición GPS", description="Eliminar (soft delete) una posición GPS.", tags=["Operations"]),
)
class GPSPositionViewSet(ModelViewSet):
    queryset = GPSPosition.objects.all()
    serializer_class = GPSPositionSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GPSPositionFilter
    ordering_fields = ["trip", "recorded_at"]
    ordering = ["trip", "recorded_at"]
