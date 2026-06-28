from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdministrator(BasePermission):
    message = "Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Administrator").exists()
        )


class IsRegularUser(BasePermission):
    message = "Esta acción requiere ser un usuario regular."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="User").exists()
        )


class ReadOnlyOrAdminWrite(BasePermission):
    message = "Solo administradores pueden crear, modificar o eliminar."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.groups.filter(name="Administrator").exists()
