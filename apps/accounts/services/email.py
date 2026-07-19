from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def _send(subject: str, to: str, txt_template: str, html_template: str, context: dict) -> None:
    text_body = render_to_string(txt_template, context)
    html_body = render_to_string(html_template, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


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
