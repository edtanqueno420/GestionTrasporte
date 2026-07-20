from django.conf import settings
from django.template.loader import render_to_string

from apps.common.services.brevo_service import send_email as brevo_send


def _send(subject: str, to: str, txt_template: str, html_template: str, context: dict) -> None:
    text_body = render_to_string(txt_template, context)
    html_body = render_to_string(html_template, context)
    brevo_send(subject, html_body, to, text_content=text_body)


def send_welcome_email(user) -> None:
    _send(
        subject="¡Bienvenido a MoviCore!",
        to=user.email,
        txt_template="emails/welcome.txt",
        html_template="emails/welcome.html",
        context={
            "username": user.username,
            "email": user.email,
        },
    )


def send_password_reset_email(user, uid: str, token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/password-reset/confirm/?uid={uid}&token={token}"
    _send(
        subject="Recuperación de contraseña — MoviCore",
        to=user.email,
        txt_template="emails/password_reset.txt",
        html_template="emails/password_reset.html",
        context={
            "username": user.username,
            "reset_url": reset_url,
        },
    )
