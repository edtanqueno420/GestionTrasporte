from django.db import models

from apps.accounts.base import BaseModel
from apps.accounts.models import User


class Notification(BaseModel):
    class Type(models.TextChoices):
        INCIDENT = "incident", "Incidente"
        SYSTEM = "system", "Sistema"
        WARNING = "warning", "Advertencia"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="usuario",
    )
    title = models.CharField("título", max_length=200)
    message = models.TextField("mensaje")
    type = models.CharField(
        "tipo", max_length=10,
        choices=Type.choices, default=Type.SYSTEM,
    )
    is_read = models.BooleanField("leído", default=False)

    class Meta:
        db_table = "notifications_notification"
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title} - {self.user}"


class UserNotificationPreference(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="notification_preferences", verbose_name="usuario",
    )
    email_enabled = models.BooleanField("notificaciones por email", default=True)
    push_enabled = models.BooleanField("notificaciones push", default=True)
    sms_enabled = models.BooleanField("notificaciones SMS", default=False)

    class Meta:
        db_table = "notifications_user_preference"
        verbose_name = "preferencia de notificación"
        verbose_name_plural = "preferencias de notificación"

    def __str__(self):
        return f"Preferencias de {self.user}"


class FCMToken(BaseModel):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        WEB = "web", "Web"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="fcm_tokens", verbose_name="usuario",
    )
    token = models.CharField("token FCM", max_length=500, unique=True)
    platform = models.CharField(
        "plataforma", max_length=10,
        choices=Platform.choices, default=Platform.WEB,
    )
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "notifications_fcm_token"
        verbose_name = "token FCM"
        verbose_name_plural = "tokens FCM"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.platform} ({self.token[:20]}...)"
