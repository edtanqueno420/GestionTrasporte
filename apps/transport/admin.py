from django.contrib import admin

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


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "transport_company", "is_active"]
    list_filter = ["is_active", "transport_company"]
    search_fields = ["code", "name"]


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "sector", "is_active"]
    list_filter = ["is_active", "sector"]
    search_fields = ["code", "name"]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate", "brand", "model", "year", "capacity", "vehicle_type", "vehicle_status", "transport_company", "is_active"]
    list_filter = ["is_active", "brand", "vehicle_type", "vehicle_status"]
    search_fields = ["plate", "brand"]


@admin.register(TransportCompany)
class TransportCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "tax_id"]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "district", "is_active"]
    list_filter = ["is_active", "district"]
    search_fields = ["code", "name"]


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(VehicleStatus)
class VehicleStatusAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(RouteBusStop)
class RouteBusStopAdmin(admin.ModelAdmin):
    list_display = ["route", "bus_stop", "stop_order", "estimated_minutes_from_start", "is_active"]
    list_filter = ["is_active", "route"]
    search_fields = ["route__code", "bus_stop__code"]
