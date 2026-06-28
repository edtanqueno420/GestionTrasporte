from rest_framework import serializers

from apps.operations.models import (
    Driver,
    DriverAssignment,
    GPSPosition,
    Maintenance,
    RouteCoordinate,
    Schedule,
    Trip,
)


class DriverSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Driver
        fields = [
            "id", "user", "user_full_name", "user_username",
            "license_number", "license_type", "hire_date",
            "experience_years", "observations", "is_available",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user_full_name", "user_username"]


class DriverAssignmentSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver.__str__", read_only=True)
    vehicle_plate = serializers.CharField(source="vehicle.plate", read_only=True)

    class Meta:
        model = DriverAssignment
        fields = [
            "id", "driver", "driver_name", "vehicle", "vehicle_plate",
            "assignment_date", "end_date", "is_active_assignment",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "driver_name", "vehicle_plate"]

    def validate(self, data):
        vehicle = data.get("vehicle", getattr(self.instance, "vehicle", None))
        is_active = data.get("is_active_assignment", getattr(self.instance, "is_active_assignment", True))

        if is_active:
            qs = DriverAssignment.objects.filter(
                vehicle=vehicle,
                is_active_assignment=True,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "El vehículo ya tiene una asignación activa."
                )
        return data

    def validate_assignment_date(self, value):
        if self.instance and self.instance.end_date and value > self.instance.end_date:
            raise serializers.ValidationError(
                "La fecha de asignación no puede ser posterior a la fecha de fin."
            )
        return value


class ScheduleSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id", "route", "route_code", "route_name",
            "departure_time", "arrival_time", "frequency_minutes", "operating_days",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "route_code", "route_name"]

    def validate(self, data):
        departure = data.get("departure_time")
        arrival = data.get("arrival_time")
        if departure and arrival and departure >= arrival:
            raise serializers.ValidationError(
                "La hora de salida debe ser anterior a la hora de llegada."
            )
        return data


class RouteCoordinateSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)

    class Meta:
        model = RouteCoordinate
        fields = [
            "id", "route", "route_code",
            "latitude", "longitude", "order",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "route_code"]

    def validate(self, data):
        route = data.get("route", getattr(self.instance, "route", None))
        order = data.get("order", getattr(self.instance, "order", None))
        if route and order is not None:
            qs = RouteCoordinate.objects.filter(route=route, order=order)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    f"Ya existe una coordenada con orden {order} para esta ruta."
                )
        return data


class MaintenanceSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source="vehicle.plate", read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            "id", "vehicle", "vehicle_plate",
            "maintenance_type", "description", "scheduled_date",
            "completed_date", "cost", "status", "observations",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "vehicle_plate"]

    def validate(self, data):
        scheduled = data.get("scheduled_date")
        completed = data.get("completed_date")
        if completed and scheduled and completed < scheduled:
            raise serializers.ValidationError(
                "La fecha de realización no puede ser anterior a la fecha programada."
            )
        status_val = data.get("status")
        if status_val == Maintenance.Status.COMPLETED and not data.get("completed_date") and not getattr(self.instance, "completed_date", None):
            raise serializers.ValidationError(
                "Debe indicar la fecha de realización para mantenimientos completados."
            )
        return data


class TripSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)
    vehicle_plate = serializers.CharField(source="vehicle.plate", read_only=True)
    driver_name = serializers.CharField(source="driver.__str__", read_only=True)
    schedule_info = serializers.CharField(source="schedule.__str__", read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id", "route", "route_code",
            "vehicle", "vehicle_plate",
            "driver", "driver_name",
            "schedule", "schedule_info",
            "trip_date", "departure_datetime", "arrival_datetime",
            "status", "passenger_count", "observations",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "route_code", "vehicle_plate", "driver_name", "schedule_info"]

    def validate(self, data):
        departure = data.get("departure_datetime")
        arrival = data.get("arrival_datetime")

        if departure and arrival and departure >= arrival:
            raise serializers.ValidationError(
                "La fecha/hora de salida debe ser anterior a la de llegada."
            )

        route = data.get("route", getattr(self.instance, "route", None))
        schedule = data.get("schedule", getattr(self.instance, "schedule", None))

        if route and schedule and schedule.route_id != route.id:
            raise serializers.ValidationError(
                "El horario no pertenece a la ruta seleccionada."
            )

        vehicle = data.get("vehicle", getattr(self.instance, "vehicle", None))
        if route and vehicle and route.transport_company_id and vehicle.transport_company_id:
            if route.transport_company_id != vehicle.transport_company_id:
                raise serializers.ValidationError(
                    "El vehículo no pertenece a la misma empresa que la ruta."
                )

        return data


class GPSPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSPosition
        fields = [
            "id", "trip", "latitude", "longitude",
            "speed", "heading", "recorded_at",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_latitude(self, value):
        if value < -90 or value > 90:
            raise serializers.ValidationError("La latitud debe estar entre -90 y 90.")
        return value

    def validate_longitude(self, value):
        if value < -180 or value > 180:
            raise serializers.ValidationError("La longitud debe estar entre -180 y 180.")
        return value

    def validate_speed(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("La velocidad no puede ser negativa.")
        return value
