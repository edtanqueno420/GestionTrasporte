from rest_framework import serializers

from apps.notifications.models import Notification, UserNotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "user", "title", "message", "type",
            "is_read", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = ["id", "user", "email_enabled", "push_enabled", "sms_enabled"]
        read_only_fields = ["id", "user"]
