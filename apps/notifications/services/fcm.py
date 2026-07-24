import logging
from pathlib import Path

from django.conf import settings
from firebase_admin import credentials, initialize_app, messaging

logger = logging.getLogger(__name__)

_app = None


def _get_app():
    global _app
    if _app is not None:
        return _app

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if not cred_path or not Path(cred_path).exists():
        logger.warning("FIREBASE_CREDENTIALS_PATH no configurado o archivo no encontrado — push deshabilitado")
        return None

    try:
        cred = credentials.Certificate(cred_path)
        _app = initialize_app(cred)
        logger.info("Firebase Admin SDK inicializado correctamente")
        return _app
    except Exception:
        logger.exception("Error inicializando Firebase Admin SDK")
        return None


def send_push_notification(token: str, title: str, body: str, data: dict | None = None) -> bool:
    app = _get_app()
    if not app:
        return False

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        data=data or {},
    )

    try:
        messaging.send(message, app=app)
        return True
    except messaging.UnregisteredError:
        logger.info("Token FCM inválido/desregistrado, desactivando: %s", token[:30])
        _deactivate_token(token)
        return False
    except messaging.SenderIdMismatchError:
        logger.warning("SenderId mismatch para token: %s", token[:30])
        _deactivate_token(token)
        return False
    except Exception:
        logger.exception("Error enviando push a token %s", token[:30])
        return False


def send_push_to_tokens(tokens: list[str], title: str, body: str, data: dict | None = None) -> dict:
    app = _get_app()
    if not app:
        return {"success": 0, "failed": len(tokens), "reason": "firebase_not_initialized"}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
        data=data or {},
    )

    try:
        response = messaging.send_each_for_multicast(message, app=app)
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    error = resp.exception
                    if isinstance(error, (messaging.UnregisteredError, messaging.SenderIdMismatchError)):
                        _deactivate_token(tokens[idx])
        return {"success": response.success_count, "failed": response.failure_count}
    except Exception:
        logger.exception("Error enviando push multicast")
        return {"success": 0, "failed": len(tokens)}


def send_push_to_user(user, title: str, body: str, data: dict | None = None) -> dict:
    from apps.notifications.models import FCMToken, UserNotificationPreference

    pref = UserNotificationPreference.objects.filter(user=user).first()
    if pref and not pref.push_enabled:
        return {"success": 0, "failed": 0, "reason": "push_disabled_by_user"}

    tokens = list(
        FCMToken.objects.filter(user=user, is_active=True).values_list("token", flat=True)
    )
    if not tokens:
        return {"success": 0, "failed": 0, "reason": "no_tokens"}

    return send_push_to_tokens(tokens, title, body, data)


def _deactivate_token(token: str):
    from apps.notifications.models import FCMToken

    FCMToken.objects.filter(token=token).update(is_active=False)
