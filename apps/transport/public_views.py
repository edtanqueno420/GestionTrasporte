from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.operations.models import RouteCoordinate
from apps.transport.models import BusStop, Route, RouteBusStop


class PublicRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "code", "name", "description"]


class PublicBusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = ["id", "code", "name", "latitude", "longitude"]


class PublicRouteCoordinateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteCoordinate
        fields = ["id", "latitude", "longitude", "order"]


class PublicRouteStopsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    stop_order = serializers.IntegerField()


class PublicRouteList(generics.ListAPIView):
    queryset = Route.objects.filter(is_active=True)
    serializer_class = PublicRouteSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Listar rutas (público)",
        description="Obtener todas las rutas activas. No requiere autenticación. Ideal para mapas y consulta ciudadana.",
        tags=["Public"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicBusStopList(generics.ListAPIView):
    queryset = BusStop.objects.filter(is_active=True)
    serializer_class = PublicBusStopSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Listar paradas (público)",
        description="Obtener todas las paradas activas con coordenadas. No requiere autenticación.",
        tags=["Public"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicRouteStops(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtener paradas de una ruta (público)",
        description="Devuelve las paradas de una ruta ordenadas por stop_order, incluyendo coordenadas. No requiere autenticación.",
        tags=["Public"],
        parameters=[
            OpenApiParameter(name="pk", location="path", required=True, type=int, description="ID de la ruta"),
        ],
        responses={
            200: OpenApiResponse(
                description="Lista de paradas ordenadas por stop_order",
                response=PublicRouteStopsSerializer(many=True),
            ),
            404: OpenApiResponse(description="Ruta no encontrada"),
        },
        examples=[
            OpenApiExample(
                name="Ejemplo respuesta",
                value=[
                    {"id": 1, "code": "BS-RIO", "name": "Terminal Río Coca", "latitude": "-0.169400", "longitude": "-78.477900", "stop_order": 1},
                    {"id": 2, "code": "BS-CAR", "name": "La Carolina", "latitude": "-0.184500", "longitude": "-78.482800", "stop_order": 2},
                ],
                response_only=True,
            ),
        ],
    )
    def get(self, request, pk):
        try:
            route = Route.objects.get(pk=pk, is_active=True)
        except Route.DoesNotExist:
            return Response({"error": "Ruta no encontrada"}, status=404)
        stops = RouteBusStop.objects.filter(
            route=route, is_active=True,
        ).select_related("bus_stop").order_by("stop_order")
        data = [
            {
                "id": rs.bus_stop.id,
                "code": rs.bus_stop.code,
                "name": rs.bus_stop.name,
                "latitude": str(rs.bus_stop.latitude),
                "longitude": str(rs.bus_stop.longitude),
                "stop_order": rs.stop_order,
            }
            for rs in stops
        ]
        return Response(data)


class PublicRouteCoordinates(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtener coordenadas de ruta (público)",
        description="Devuelve los puntos de coordenadas de una ruta ordenados para dibujar una polyline en el mapa. No requiere autenticación.",
        tags=["Public"],
        parameters=[
            OpenApiParameter(name="pk", location="path", required=True, type=int, description="ID de la ruta"),
        ],
        responses={
            200: OpenApiResponse(
                description="Array de puntos coordenados ordenados por order",
                response=PublicRouteCoordinateSerializer(many=True),
            ),
            404: OpenApiResponse(description="Ruta no encontrada"),
        },
        examples=[
            OpenApiExample(
                name="Ejemplo respuesta",
                value=[
                    {"id": 1, "latitude": "-0.169400", "longitude": "-78.477900", "order": 1},
                    {"id": 2, "latitude": "-0.173175", "longitude": "-78.479125", "order": 2},
                ],
                response_only=True,
            ),
        ],
    )
    def get(self, request, pk):
        try:
            route = Route.objects.get(pk=pk, is_active=True)
        except Route.DoesNotExist:
            return Response({"error": "Ruta no encontrada"}, status=404)
        coords = RouteCoordinate.objects.filter(
            route=route, is_active=True,
        ).order_by("order")
        data = [
            {
                "id": c.id,
                "latitude": str(c.latitude),
                "longitude": str(c.longitude),
                "order": c.order,
            }
            for c in coords
        ]
        return Response(data)
