from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.base import BaseModel, SoftDeleteModel


class District(BaseModel, SoftDeleteModel):
    name = models.CharField("nombre", max_length=200)
    code = models.CharField("código", max_length=20, unique=True)

    class Meta:
        db_table = "transport_district"
        verbose_name = "distrito"
        verbose_name_plural = "distritos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Sector(BaseModel, SoftDeleteModel):
    district = models.ForeignKey(
        District, on_delete=models.PROTECT,
        related_name="sectors", verbose_name="distrito",
    )
    name = models.CharField("nombre", max_length=200)
    code = models.CharField("código", max_length=20, unique=True)

    class Meta:
        db_table = "transport_sector"
        verbose_name = "sector"
        verbose_name_plural = "sectores"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.district.code})"


class TransportCompany(BaseModel, SoftDeleteModel):
    name = models.CharField("nombre", max_length=200)
    tax_id = models.CharField("ruc", max_length=20, unique=True)
    phone = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo electrónico", blank=True)
    address = models.CharField("dirección", max_length=300, blank=True)

    class Meta:
        db_table = "transport_company"
        verbose_name = "empresa de transporte"
        verbose_name_plural = "empresas de transporte"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class VehicleType(BaseModel, SoftDeleteModel):
    name = models.CharField("nombre", max_length=100)
    code = models.CharField("código", max_length=20, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        db_table = "transport_vehicle_type"
        verbose_name = "tipo de vehículo"
        verbose_name_plural = "tipos de vehículo"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class VehicleStatus(BaseModel, SoftDeleteModel):
    name = models.CharField("nombre", max_length=100)
    code = models.CharField("código", max_length=20, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        db_table = "transport_vehicle_status"
        verbose_name = "estado de vehículo"
        verbose_name_plural = "estados de vehículo"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Route(BaseModel, SoftDeleteModel):
    code = models.CharField("código", max_length=20, unique=True)
    name = models.CharField("nombre", max_length=200)
    description = models.TextField("descripción", blank=True)
    transport_company = models.ForeignKey(
        TransportCompany, on_delete=models.PROTECT,
        related_name="routes", verbose_name="empresa",
        null=True, blank=True,
    )
    bus_stops = models.ManyToManyField(
        "BusStop",
        through="RouteBusStop",
        through_fields=("route", "bus_stop"),
        related_name="routes",
        verbose_name="paradas",
    )

    class Meta:
        db_table = "transport_route"
        verbose_name = "ruta"
        verbose_name_plural = "rutas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class RouteBusStop(BaseModel, SoftDeleteModel):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE,
        related_name="route_stops", verbose_name="ruta",
    )
    bus_stop = models.ForeignKey(
        "BusStop", on_delete=models.CASCADE,
        related_name="stop_routes", verbose_name="parada",
    )
    stop_order = models.PositiveIntegerField("orden")
    estimated_minutes_from_start = models.PositiveIntegerField(
        "minutos estimados desde inicio", null=True, blank=True,
    )

    class Meta:
        db_table = "transport_route_bus_stop"
        verbose_name = "parada de ruta"
        verbose_name_plural = "paradas de ruta"
        ordering = ["stop_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["route", "stop_order"],
                name="uq_route_stop_order",
            ),
            models.UniqueConstraint(
                fields=["route", "bus_stop"],
                name="uq_route_bus_stop",
            ),
        ]

    def __str__(self):
        return f"{self.route.code} - {self.bus_stop.code} (orden {self.stop_order})"


class BusStop(BaseModel, SoftDeleteModel):
    code = models.CharField("código", max_length=20, unique=True)
    name = models.CharField("nombre", max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT,
        related_name="bus_stops", verbose_name="sector",
        null=True, blank=True,
    )

    class Meta:
        db_table = "transport_bus_stop"
        verbose_name = "parada"
        verbose_name_plural = "paradas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Vehicle(BaseModel, SoftDeleteModel):
    plate = models.CharField("placa", max_length=10, unique=True)
    brand = models.CharField("marca", max_length=100)
    model = models.CharField("modelo", max_length=100)
    year = models.PositiveIntegerField(
        "año",
        validators=[MinValueValidator(1950), MaxValueValidator(2100)],
    )
    capacity = models.PositiveIntegerField(
        "capacidad",
        validators=[MinValueValidator(1)],
    )
    transport_company = models.ForeignKey(
        TransportCompany, on_delete=models.PROTECT,
        related_name="vehicles", verbose_name="empresa",
        null=True, blank=True,
    )
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.PROTECT,
        related_name="vehicles", verbose_name="tipo",
        null=True, blank=True,
    )
    vehicle_status = models.ForeignKey(
        VehicleStatus, on_delete=models.PROTECT,
        related_name="vehicles", verbose_name="estado",
        null=True, blank=True,
    )

    class Meta:
        db_table = "transport_vehicle"
        verbose_name = "vehículo"
        verbose_name_plural = "vehículos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"
