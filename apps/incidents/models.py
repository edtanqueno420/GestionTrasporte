from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.base import BaseModel, SoftDeleteModel
from apps.accounts.models import User
from apps.operations.models import Driver, Trip
from apps.transport.models import Vehicle


class IncidentType(BaseModel, SoftDeleteModel):
    name = models.CharField("nombre", max_length=100)
    code = models.CharField("código", max_length=20, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        db_table = "incidents_incident_type"
        verbose_name = "tipo de incidente"
        verbose_name_plural = "tipos de incidente"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Incident(BaseModel, SoftDeleteModel):
    class Severity(models.TextChoices):
        LOW = "low", "Baja"
        MEDIUM = "medium", "Media"
        HIGH = "high", "Alta"

    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        IN_PROGRESS = "in_progress", "En Progreso"
        RESOLVED = "resolved", "Resuelto"

    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE,
        related_name="incidents", verbose_name="viaje",
    )
    incident_type = models.ForeignKey(
        IncidentType, on_delete=models.PROTECT,
        related_name="incidents", verbose_name="tipo",
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT,
        related_name="incidents", verbose_name="vehículo",
        null=True, blank=True,
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT,
        related_name="incidents", verbose_name="conductor",
        null=True, blank=True,
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    description = models.TextField("descripción", blank=True)
    severity = models.CharField(
        "severidad", max_length=10,
        choices=Severity.choices, default=Severity.MEDIUM,
    )
    status = models.CharField(
        "estado", max_length=15,
        choices=Status.choices, default=Status.OPEN,
    )
    resolved_at = models.DateTimeField("fecha de resolución", null=True, blank=True)

    class Meta:
        db_table = "incidents_incident"
        verbose_name = "incidente"
        verbose_name_plural = "incidentes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_severity_display()} - {self.incident_type.name} ({self.trip})"
