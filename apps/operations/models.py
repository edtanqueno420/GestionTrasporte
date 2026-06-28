from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, UniqueConstraint

from apps.accounts.base import BaseModel, SoftDeleteModel
from apps.accounts.models import User
from apps.transport.models import Route, Vehicle


class Driver(BaseModel, SoftDeleteModel):
    class LicenseType(models.TextChoices):
        A = "A", "Tipo A (Automóvil)"
        B = "B", "Tipo B (Camioneta)"
        C = "C", "Tipo C (Bus)"
        D = "D", "Tipo D (Camión)"
        E = "E", "Tipo E (Pesado)"

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="driver", verbose_name="usuario",
    )
    license_number = models.CharField("licencia", max_length=30, unique=True)
    license_type = models.CharField(
        "tipo de licencia", max_length=1,
        choices=LicenseType.choices, default=LicenseType.C,
    )
    hire_date = models.DateField("fecha de contratación")
    experience_years = models.PositiveIntegerField(
        "años de experiencia", default=0,
        validators=[MinValueValidator(0)],
    )
    observations = models.TextField("observaciones", blank=True)
    is_available = models.BooleanField("disponible", default=True)

    class Meta:
        db_table = "operations_driver"
        verbose_name = "conductor"
        verbose_name_plural = "conductores"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.license_number})"


class DriverAssignment(BaseModel, SoftDeleteModel):
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT,
        related_name="assignments", verbose_name="conductor",
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT,
        related_name="assignments", verbose_name="vehículo",
    )
    assignment_date = models.DateField("fecha de asignación")
    end_date = models.DateField("fecha de fin", null=True, blank=True)
    is_active_assignment = models.BooleanField("asignación activa", default=True)

    class Meta:
        db_table = "operations_driver_assignment"
        verbose_name = "asignación de conductor"
        verbose_name_plural = "asignaciones de conductores"
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["vehicle"],
                condition=Q(is_active_assignment=True, is_active=True),
                name="uq_vehicle_active_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.driver} → {self.vehicle.plate} ({self.assignment_date})"


class Schedule(BaseModel, SoftDeleteModel):
    route = models.ForeignKey(
        Route, on_delete=models.PROTECT,
        related_name="schedules", verbose_name="ruta",
    )
    departure_time = models.TimeField("hora de salida")
    arrival_time = models.TimeField("hora de llegada")
    frequency_minutes = models.PositiveIntegerField(
        "frecuencia (minutos)",
        validators=[MinValueValidator(1)],
    )
    operating_days = models.CharField(
        "días de operación",
        max_length=7,
        validators=[
            RegexValidator(r"^[1-7]+$", "Use dígitos 1-7 donde 1=Lunes, 7=Domingo"),
        ],
    )

    class Meta:
        db_table = "operations_schedule"
        verbose_name = "horario"
        verbose_name_plural = "horarios"
        ordering = ["route", "departure_time"]

    def __str__(self):
        return f"{self.route.code} ({self.departure_time} - {self.arrival_time})"


class RouteCoordinate(BaseModel, SoftDeleteModel):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE,
        related_name="coordinates", verbose_name="ruta",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    order = models.PositiveIntegerField("orden")

    class Meta:
        db_table = "operations_route_coordinate"
        verbose_name = "coordenada de ruta"
        verbose_name_plural = "coordenadas de ruta"
        ordering = ["route", "order"]
        constraints = [
            UniqueConstraint(
                fields=["route", "order"],
                name="uq_route_coordinate_order",
            ),
        ]

    def __str__(self):
        return f"{self.route.code} - punto {self.order}"


class Maintenance(BaseModel, SoftDeleteModel):
    class MaintenanceType(models.TextChoices):
        PREVENTIVE = "preventive", "Preventivo"
        CORRECTIVE = "corrective", "Correctivo"
        PREDICTIVE = "predictive", "Predictivo"
        EMERGENCY = "emergency", "Emergencia"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Programado"
        IN_PROGRESS = "in_progress", "En Progreso"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT,
        related_name="maintenances", verbose_name="vehículo",
    )
    maintenance_type = models.CharField(
        "tipo de mantenimiento", max_length=20,
        choices=MaintenanceType.choices, default=MaintenanceType.PREVENTIVE,
    )
    description = models.TextField("descripción")
    scheduled_date = models.DateField("fecha programada")
    completed_date = models.DateField("fecha de realización", null=True, blank=True)
    cost = models.DecimalField(
        "costo", max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    status = models.CharField(
        "estado", max_length=20,
        choices=Status.choices, default=Status.SCHEDULED,
    )
    observations = models.TextField("observaciones", blank=True)

    class Meta:
        db_table = "operations_maintenance"
        verbose_name = "mantenimiento"
        verbose_name_plural = "mantenimientos"
        ordering = ["-scheduled_date", "-created_at"]

    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_maintenance_type_display()} ({self.get_status_display()})"


class Trip(BaseModel, SoftDeleteModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Programado"
        IN_PROGRESS = "in_progress", "En Progreso"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    route = models.ForeignKey(
        Route, on_delete=models.PROTECT,
        related_name="trips", verbose_name="ruta",
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT,
        related_name="trips", verbose_name="vehículo",
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT,
        related_name="trips", verbose_name="conductor",
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.PROTECT,
        related_name="trips", verbose_name="horario",
        null=True, blank=True,
    )
    trip_date = models.DateField("fecha del viaje")
    departure_datetime = models.DateTimeField("salida")
    arrival_datetime = models.DateTimeField("llegada", null=True, blank=True)
    status = models.CharField(
        "estado", max_length=20,
        choices=Status.choices, default=Status.SCHEDULED,
    )
    passenger_count = models.PositiveIntegerField(
        "pasajeros", null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    observations = models.TextField("observaciones", blank=True)

    class Meta:
        db_table = "operations_trip"
        verbose_name = "viaje"
        verbose_name_plural = "viajes"
        ordering = ["-trip_date", "-departure_datetime"]

    def __str__(self):
        return f"{self.route.code} - {self.vehicle.plate} ({self.trip_date} {self.departure_datetime})"


class GPSPosition(BaseModel, SoftDeleteModel):
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE,
        related_name="positions", verbose_name="viaje",
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    speed = models.DecimalField(
        "velocidad (km/h)", max_digits=6, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    heading = models.DecimalField(
        "rumbo (°)", max_digits=5, decimal_places=2,
        null=True, blank=True,
    )
    recorded_at = models.DateTimeField("fecha/hora del registro")

    class Meta:
        db_table = "operations_gps_position"
        verbose_name = "posición GPS"
        verbose_name_plural = "posiciones GPS"
        ordering = ["trip", "recorded_at"]

    def __str__(self):
        return f"{self.trip} - ({self.latitude}, {self.longitude}) @ {self.recorded_at}"
