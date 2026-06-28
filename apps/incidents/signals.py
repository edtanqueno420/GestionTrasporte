from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.incidents.models import Incident
from apps.notifications.models import Notification


@receiver(post_save, sender=Incident)
def notify_on_incident(sender, instance, created, **kwargs):
    if not created:
        return

    admin_group = Group.objects.filter(name="Administrator").first()
    if not admin_group:
        return

    incident_type_name = instance.incident_type.name
    for admin_user in admin_group.user_set.all():
        Notification.objects.create(
            user=admin_user,
            title=f"Nuevo Incidente: {incident_type_name}",
            message=(
                f"Incidente {incident_type_name} registrado en el viaje "
                f"{instance.trip} ({instance.get_severity_display()})."
            ),
            type=Notification.Type.INCIDENT,
        )
