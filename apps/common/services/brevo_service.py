import logging

from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration, SendSmtpEmail, TransactionalEmailsApi

logger = logging.getLogger(__name__)


def _parse_from_email():
    """Extrae name y email de DEFAULT_FROM_EMAIL (formato: 'Name <email>')."""
    raw = settings.DEFAULT_FROM_EMAIL
    if "<" in raw and ">" in raw:
        name = raw[: raw.index("<")].strip()
        email = raw[raw.index("<") + 1 : raw.index(">")]
        return {"name": name, "email": email}
    return {"name": "MoviCore", "email": raw}


def send_email(subject: str, html_content: str, recipient: str, text_content: str | None = None) -> None:
    configuration = Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY
    api_instance = TransactionalEmailsApi(ApiClient(configuration))

    kwargs = {
        "sender": _parse_from_email(),
        "to": [{"email": recipient}],
        "subject": subject,
        "html_content": html_content,
    }
    if text_content:
        kwargs["text_content"] = text_content

    email = SendSmtpEmail(**kwargs)
    api_instance.send_transac_email(email)