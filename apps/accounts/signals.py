import logging

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Profile, User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    if created:
        user_group, _ = Group.objects.get_or_create(name="User")
        instance.groups.add(user_group)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def send_welcome(sender, instance, created, **kwargs):
    if created and instance.email:
        try:
            from apps.accounts.services.email import send_welcome_email
            send_welcome_email(instance)
        except Exception:
            logger.exception("Error enviando correo de bienvenida a %s", instance.email)
