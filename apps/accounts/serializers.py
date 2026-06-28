from django.contrib.auth import password_validation
from django.contrib.auth.models import Group
from rest_framework import serializers

from apps.accounts.models import AuditLog, Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar_url", "address", "emergency_contact", "emergency_phone"]


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        slug_field="name", many=True, read_only=True,
    )
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "is_active", "groups", "date_joined", "updated_at",
            "profile",
        ]
        read_only_fields = ["id", "groups", "date_joined", "updated_at", "profile"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name", "phone"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "user", "action", "detail", "created_at"]
        read_only_fields = ["id", "created_at"]
