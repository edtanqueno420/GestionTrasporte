from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.incidents.models import Incident, IncidentType


class IncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentType
        fields = ["id", "name", "code", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            "id", "trip", "incident_type", "vehicle", "driver",
            "latitude", "longitude", "description", "severity",
            "status", "resolved_at", "is_active",
            "created_at", "updated_at",
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


class IncidentListSerializer(serializers.ModelSerializer):
    incident_type_name = serializers.CharField(source="incident_type.name", read_only=True)
    trip_info = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id", "trip", "trip_info", "incident_type", "incident_type_name",
            "latitude", "longitude", "description", "severity",
            "status", "resolved_at", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(str)
    def get_trip_info(self, obj):
        return str(obj.trip)
