from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea los grupos iniciales y asigna permisos por app"

    TARGET_APPS = ["accounts", "transport", "incidents", "operations", "notifications"]

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name="Administrator")
        user_group, _ = Group.objects.get_or_create(name="User")

        admin_perms = Permission.objects.filter(
            content_type__app_label__in=self.TARGET_APPS,
        ).select_related("content_type")
        admin_group.permissions.set(list(admin_perms))

        user_view_perms = Permission.objects.filter(
            content_type__app_label__in=self.TARGET_APPS,
            codename__startswith="view_",
        )
        user_group.permissions.set(list(user_view_perms))

        self.stdout.write(self.style.SUCCESS(
            f"Groups created: Administrator ({admin_group.permissions.count()} perms), "
            f"User ({user_group.permissions.count()} perms)"
        ))
