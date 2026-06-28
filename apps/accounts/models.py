from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.base import BaseModel


class User(AbstractUser):
    phone = models.CharField("teléfono", max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_user"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        permissions = [
            ("can_manage_users", "Puede gestionar usuarios del sistema"),
        ]

    def __str__(self):
        return self.get_full_name() or self.username


class Profile(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="profile", verbose_name="usuario",
    )
    avatar_url = models.URLField("avatar", max_length=500, blank=True)
    address = models.CharField("dirección", max_length=300, blank=True)
    emergency_contact = models.CharField("contacto de emergencia", max_length=200, blank=True)
    emergency_phone = models.CharField("teléfono de emergencia", max_length=20, blank=True)

    class Meta:
        db_table = "accounts_profile"
        verbose_name = "perfil"
        verbose_name_plural = "perfiles"

    def __str__(self):
        return f"Perfil de {self.user}"


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Inicio de sesión"
        REGISTER = "register", "Registro"
        PASSWORD_CHANGE = "password_change", "Cambio de contraseña"
        ADMIN_ACTION = "admin_action", "Acción administrativa"

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="usuario",
    )
    action = models.CharField("acción", max_length=30, choices=Action.choices)
    detail = models.TextField("detalle", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_audit_log"
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.user} ({self.created_at})"
