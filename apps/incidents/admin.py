from django.contrib import admin

from apps.incidents.models import Incident, IncidentType


@admin.register(IncidentType)
class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["incident_type", "severity", "status", "trip", "created_at"]
    list_filter = ["severity", "status", "incident_type"]
    search_fields = ["description", "trip__route__code"]
