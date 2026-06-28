from django.contrib import admin

from apps.operations.models import (
    Driver,
    DriverAssignment,
    GPSPosition,
    Maintenance,
    RouteCoordinate,
    Schedule,
    Trip,
)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["user", "license_number", "license_type", "hire_date", "is_available", "is_active"]
    list_filter = ["is_available", "is_active", "license_type"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "license_number"]


@admin.register(DriverAssignment)
class DriverAssignmentAdmin(admin.ModelAdmin):
    list_display = ["driver", "vehicle", "assignment_date", "end_date", "is_active_assignment"]
    list_filter = ["is_active_assignment"]
    search_fields = ["driver__user__username", "vehicle__plate"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["route", "departure_time", "arrival_time", "frequency_minutes", "operating_days", "is_active"]
    list_filter = ["is_active", "route"]
    search_fields = ["route__code", "route__name"]


@admin.register(RouteCoordinate)
class RouteCoordinateAdmin(admin.ModelAdmin):
    list_display = ["route", "order", "latitude", "longitude", "is_active"]
    list_filter = ["route"]
    search_fields = ["route__code"]


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "maintenance_type", "status", "scheduled_date", "completed_date", "cost"]
    list_filter = ["maintenance_type", "status", "vehicle"]
    search_fields = ["vehicle__plate", "description"]


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["route", "vehicle", "driver", "trip_date", "departure_datetime", "status"]
    list_filter = ["status", "trip_date", "route"]
    search_fields = ["route__code", "vehicle__plate", "driver__user__username"]
    ordering = ["-trip_date"]


@admin.register(GPSPosition)
class GPSPositionAdmin(admin.ModelAdmin):
    list_display = ["trip", "latitude", "longitude", "speed", "recorded_at"]
    list_filter = ["trip"]
    search_fields = ["trip__route__code"]
