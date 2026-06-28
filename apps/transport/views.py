from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadOnlyOrAdminWrite
from apps.transport.models import (
    BusStop,
    District,
    Route,
    RouteBusStop,
    Sector,
    TransportCompany,
    Vehicle,
    VehicleStatus,
    VehicleType,
)
from apps.transport.serializers import (
    BusStopSerializer,
    DistrictSerializer,
    RouteBusStopSerializer,
    RouteSerializer,
    SectorSerializer,
    TransportCompanySerializer,
    VehicleSerializer,
    VehicleStatusSerializer,
    VehicleTypeSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Listar empresas de transporte", description="Obtener listado paginado de empresas de transporte. Filtrable por búsqueda (nombre, RUC).", tags=["Transport"]),
    create=extend_schema(summary="Crear empresa de transporte", description="Registrar una nueva empresa de transporte con su información fiscal.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener empresa de transporte", description="Obtener detalle de una empresa por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar empresa de transporte", description="Reemplazar todos los datos de una empresa.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente empresa de transporte", description="Actualizar campos específicos de una empresa.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar empresa de transporte", description="Eliminar (soft delete) una empresa de transporte.", tags=["Transport"]),
)
class TransportCompanyViewSet(ModelViewSet):
    queryset = TransportCompany.objects.all()
    serializer_class = TransportCompanySerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "tax_id"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar distritos", description="Obtener listado paginado de distritos metropolitanos.", tags=["Transport"]),
    create=extend_schema(summary="Crear distrito", description="Registrar un nuevo distrito metropolitano.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener distrito", description="Obtener detalle de un distrito por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar distrito", description="Reemplazar todos los datos de un distrito.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente distrito", description="Actualizar campos específicos de un distrito.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar distrito", description="Eliminar (soft delete) un distrito.", tags=["Transport"]),
)
class DistrictViewSet(ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar sectores", description="Obtener listado paginado de sectores. Filtrable por distrito.", tags=["Transport"]),
    create=extend_schema(summary="Crear sector", description="Registrar un nuevo sector dentro de un distrito.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener sector", description="Obtener detalle de un sector por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar sector", description="Reemplazar todos los datos de un sector.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente sector", description="Actualizar campos específicos de un sector.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar sector", description="Eliminar (soft delete) un sector.", tags=["Transport"]),
)
class SectorViewSet(ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["district"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar tipos de vehículo", description="Obtener listado paginado de tipos de vehículo (articulado, alimentador, etc.).", tags=["Transport"]),
    create=extend_schema(summary="Crear tipo de vehículo", description="Registrar un nuevo tipo de vehículo.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener tipo de vehículo", description="Obtener detalle de un tipo de vehículo por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar tipo de vehículo", description="Reemplazar todos los datos de un tipo de vehículo.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente tipo de vehículo", description="Actualizar campos específicos de un tipo de vehículo.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar tipo de vehículo", description="Eliminar (soft delete) un tipo de vehículo.", tags=["Transport"]),
)
class VehicleTypeViewSet(ModelViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar estados de vehículo", description="Obtener listado paginado de estados de vehículo (activo, en mantenimiento, etc.).", tags=["Transport"]),
    create=extend_schema(summary="Crear estado de vehículo", description="Registrar un nuevo estado de vehículo.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener estado de vehículo", description="Obtener detalle de un estado de vehículo por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar estado de vehículo", description="Reemplazar todos los datos de un estado.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente estado de vehículo", description="Actualizar campos específicos de un estado.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar estado de vehículo", description="Eliminar (soft delete) un estado de vehículo.", tags=["Transport"]),
)
class VehicleStatusViewSet(ModelViewSet):
    queryset = VehicleStatus.objects.all()
    serializer_class = VehicleStatusSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar rutas", description="Obtener listado paginado de rutas de transporte. Filtrable por empresa y búsqueda por código/nombre.", tags=["Transport"]),
    create=extend_schema(summary="Crear ruta", description="Registrar una nueva ruta de transporte con su código y nombre.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener ruta", description="Obtener detalle de una ruta por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar ruta", description="Reemplazar todos los datos de una ruta.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente ruta", description="Actualizar campos específicos de una ruta.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar ruta", description="Eliminar (soft delete) una ruta.", tags=["Transport"]),
)
class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["transport_company"]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar paradas", description="Obtener listado paginado de paradas de buses. Filtrable por sector y búsqueda por código/nombre.", tags=["Transport"]),
    create=extend_schema(summary="Crear parada", description="Registrar una nueva parada con coordenadas geográficas.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener parada", description="Obtener detalle de una parada por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar parada", description="Reemplazar todos los datos de una parada.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente parada", description="Actualizar campos específicos de una parada.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar parada", description="Eliminar (soft delete) una parada.", tags=["Transport"]),
)
class BusStopViewSet(ModelViewSet):
    queryset = BusStop.objects.all()
    serializer_class = BusStopSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["sector"]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar vehículos", description="Obtener listado paginado de vehículos. Filtrable por empresa, tipo y estado. Búsqueda por placa, marca, modelo.", tags=["Transport"]),
    create=extend_schema(summary="Crear vehículo", description="Registrar un nuevo vehículo con placa única, marca, modelo y capacidad.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener vehículo", description="Obtener detalle de un vehículo por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar vehículo", description="Reemplazar todos los datos de un vehículo.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente vehículo", description="Actualizar campos específicos de un vehículo.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar vehículo", description="Eliminar (soft delete) un vehículo.", tags=["Transport"]),
)
class VehicleViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["transport_company", "vehicle_type", "vehicle_status"]
    search_fields = ["plate", "brand", "model"]
    ordering_fields = ["plate", "brand", "year", "created_at"]
    ordering = ["-created_at"]


@extend_schema_view(
    list=extend_schema(summary="Listar asignaciones ruta-parada", description="Obtener listado paginado de asignaciones de paradas a rutas. Filtrable por ruta.", tags=["Transport"]),
    create=extend_schema(summary="Asignar parada a ruta", description="Asignar una parada a una ruta con un orden específico.", tags=["Transport"]),
    retrieve=extend_schema(summary="Obtener asignación ruta-parada", description="Obtener detalle de una asignación por su ID.", tags=["Transport"]),
    update=extend_schema(summary="Actualizar asignación ruta-parada", description="Reemplazar todos los datos de una asignación.", tags=["Transport"]),
    partial_update=extend_schema(summary="Actualizar parcialmente asignación", description="Cambiar el orden de una parada en una ruta.", tags=["Transport"]),
    destroy=extend_schema(summary="Eliminar asignación ruta-parada", description="Eliminar (soft delete) una asignación de parada de ruta.", tags=["Transport"]),
)
class RouteBusStopViewSet(ModelViewSet):
    queryset = RouteBusStop.objects.all()
    serializer_class = RouteBusStopSerializer
    permission_classes = [ReadOnlyOrAdminWrite]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["route"]
    ordering_fields = ["route", "stop_order"]
    ordering = ["stop_order"]
