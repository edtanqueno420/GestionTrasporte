from rest_framework import serializers

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


class TransportCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportCompany
        fields = ["id", "name", "tax_id", "phone", "email", "address", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name", "code", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SectorSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)

    class Meta:
        model = Sector
        fields = ["id", "district", "district_name", "name", "code", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "name", "code", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleStatus
        fields = ["id", "name", "code", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteSerializer(serializers.ModelSerializer):
    transport_company_name = serializers.CharField(source="transport_company.name", read_only=True)

    class Meta:
        model = Route
        fields = [
            "id", "code", "name", "description",
            "transport_company", "transport_company_name",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BusStopSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source="sector.name", read_only=True)

    class Meta:
        model = BusStop
        fields = [
            "id", "code", "name", "latitude", "longitude",
            "sector", "sector_name",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VehicleSerializer(serializers.ModelSerializer):
    transport_company_name = serializers.CharField(source="transport_company.name", read_only=True)
    vehicle_type_name = serializers.CharField(source="vehicle_type.name", read_only=True)
    vehicle_status_name = serializers.CharField(source="vehicle_status.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id", "plate", "brand", "model", "year", "capacity",
            "transport_company", "transport_company_name",
            "vehicle_type", "vehicle_type_name",
            "vehicle_status", "vehicle_status_name",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RouteBusStopSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)
    bus_stop_code = serializers.CharField(source="bus_stop.code", read_only=True)
    bus_stop_name = serializers.CharField(source="bus_stop.name", read_only=True)

    class Meta:
        model = RouteBusStop
        fields = [
            "id", "route", "route_code",
            "bus_stop", "bus_stop_code", "bus_stop_name",
            "stop_order", "estimated_minutes_from_start",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "route_code", "bus_stop_code", "bus_stop_name"]

    def validate(self, data):
        route = data.get("route", getattr(self.instance, "route", None))
        stop_order = data.get("stop_order", getattr(self.instance, "stop_order", None))

        if route and stop_order is not None:
            qs = RouteBusStop.objects.filter(route=route, stop_order=stop_order)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"Ya existe una parada con orden {stop_order} para esta ruta."
                )

        bus_stop = data.get("bus_stop", getattr(self.instance, "bus_stop", None))
        if route and bus_stop:
            qs = RouteBusStop.objects.filter(route=route, bus_stop=bus_stop)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Esta parada ya está registrada en la ruta."
                )

        return data
