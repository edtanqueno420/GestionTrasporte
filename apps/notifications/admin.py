from django.contrib import admin

from apps.notifications.models import Notification, UserNotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "type", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    search_fields = ["title", "message", "user__username"]


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "email_enabled", "push_enabled", "sms_enabled"]
