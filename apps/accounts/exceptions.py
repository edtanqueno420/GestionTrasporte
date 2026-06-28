from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        errors = response.data
        if isinstance(errors, dict):
            first_error = _get_first_error(errors)
        elif isinstance(errors, list):
            first_error = str(errors[0]) if errors else "Error desconocido"
        else:
            first_error = str(errors)

        response.data = {
            "success": False,
            "message": first_error,
            "errors": errors,
        }
    else:
        response = _unhandled_error_response(exc)

    return response


def _get_first_error(errors):
    if isinstance(errors, dict):
        for field, msgs in errors.items():
            if isinstance(msgs, list):
                return str(msgs[0])
            if isinstance(msgs, str):
                return msgs
            if isinstance(msgs, dict):
                return _get_first_error(msgs)
    return "Error de validación"


def _unhandled_error_response(exc):
    from rest_framework.response import Response
    from rest_framework import status

    if isinstance(exc, APIException):
        return Response(
            {"success": False, "message": str(exc), "errors": {}},
            status=exc.status_code,
        )

    if isinstance(exc, Exception):
        return Response(
            {"success": False, "message": "Error interno del servidor", "errors": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return None
