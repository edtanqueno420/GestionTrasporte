from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import ReadOnlyOrAdminWrite
from apps.notifications.models import Notification
from apps.notifications.permissions import IsRecipientOrAdmin
from apps.notifications.serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Listar notificaciones",
        description="Obtener notificaciones del usuario autenticado. Los administradores ven todas. Incluye conteo de no leídas en la respuesta.",
        tags=["Notifications"],
        parameters=[
            OpenApiParameter(name="is_read", type=bool, description="Filtrar por leídas (true) o no leídas (false)"),
            OpenApiParameter(name="type", type=str, description="Filtrar por tipo (incident/system/warning)"),
        ],
    ),
    create=extend_schema(summary="Crear notificación", description="Crear una notificación para un usuario.", tags=["Notifications"]),
    retrieve=extend_schema(summary="Obtener notificación", description="Obtener detalle de una notificación por su ID.", tags=["Notifications"]),
    update=extend_schema(summary="Actualizar notificación", description="Reemplazar todos los datos de una notificación.", tags=["Notifications"]),
    partial_update=extend_schema(summary="Actualizar parcialmente notificación", description="Actualizar campos de una notificación.", tags=["Notifications"]),
    destroy=extend_schema(summary="Eliminar notificación", description="Eliminar una notificación.", tags=["Notifications"]),
)
class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsRecipientOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_read", "type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Notification.objects.all()
        user = self.request.user
        if not user.groups.filter(name="Administrator").exists():
            qs = qs.filter(user=user)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            unread_count = self.get_queryset().filter(is_read=False).count()
            response.data["unread_count"] = unread_count
            return response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Marcar notificación como leída",
        description="Marcar una notificación específica como leída.",
        tags=["Notifications"],
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @extend_schema(
        summary="Marcar todas como leídas",
        description="Marcar todas las notificaciones no leídas del usuario como leídas.",
        tags=["Notifications"],
        responses={200: OpenApiResponse(description="Cantidad de notificaciones marcadas")},
        examples=[
            OpenApiExample(
                name="Todas marcadas",
                value={"marked_read": 3},
                response_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["put"])
    def read_all(self, request):
        qs = self.get_queryset().filter(is_read=False)
        count = qs.update(is_read=True)
        return Response({"marked_read": count})
