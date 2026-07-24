from rest_framework import serializers

from apps.notifications.models import FCMToken, Notification, UserNotificationPreference


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


class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ["id", "token", "platform", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def create(self, validated_data):
        token = validated_data["token"]
        validated_data["user"] = self.context["request"].user
        obj, created = FCMToken.objects.update_or_create(
            token=token,
            defaults={
                "user": validated_data["user"],
                "platform": validated_data["platform"],
                "is_active": True,
            },
        )
        return obj
