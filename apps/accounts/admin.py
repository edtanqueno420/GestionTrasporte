from django.contrib import admin

from apps.accounts.models import AuditLog, Profile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "is_active", "group_names"]
    list_filter = ["is_active", "groups"]
    search_fields = ["username", "email", "first_name", "last_name"]

    def group_names(self, obj):
        return ", ".join(g.name for g in obj.groups.all())

    group_names.short_description = "grupos"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "address", "emergency_contact"]
    search_fields = ["user__username", "user__email"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "user", "created_at"]
    list_filter = ["action"]
    search_fields = ["user__username", "detail"]
    readonly_fields = ["user", "action", "detail", "created_at"]
