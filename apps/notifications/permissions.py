from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsRecipientOrAdmin(BasePermission):
    message = "Solo puedes ver tus propias notificaciones."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user_is_recipient = obj.user == request.user
        is_admin = request.user.groups.filter(name="Administrator").exists()

        if request.method in SAFE_METHODS:
            return user_is_recipient or is_admin

        if request.method == "PATCH" and user_is_recipient:
            return True

        return is_admin
