from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.incidents.models import Incident
from apps.notifications.models import Notification
from apps.notifications.services.fcm import send_push_to_user


@receiver(post_save, sender=Incident)
def notify_on_incident(sender, instance, created, **kwargs):
    if not created:
        return

    admin_group = Group.objects.filter(name="Administrator").first()
    if not admin_group:
        return

    incident_type_name = instance.incident_type.name
    push_title = f"Nuevo Incidente: {incident_type_name}"
    push_body = (
        f"Incidente {incident_type_name} registrado en el viaje "
        f"{instance.trip} ({instance.get_severity_display()})."
    )

    for admin_user in admin_group.user_set.all():
        Notification.objects.create(
            user=admin_user,
            title=push_title,
            message=push_body,
            type=Notification.Type.INCIDENT,
        )

        try:
            send_push_to_user(
                admin_user,
                title=push_title,
                body=push_body,
                data={
                    "type": "incident",
                    "incident_id": str(instance.id),
                    "severity": instance.severity,
                },
            )
        except Exception:
            pass
