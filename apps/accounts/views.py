from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import AuditLog, Profile
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Health Check",
        description="Verificar el estado operativo del servicio",
        tags=["Auth"],
        responses={
            200: OpenApiResponse(
                description="Servicio operativo",
                response={"type": "object", "properties": {
                    "status": {"type": "string", "example": "ok"},
                    "service": {"type": "string", "example": "QuitoMove Smart Mobility"},
                }},
            ),
        },
    )
    def get(self, request):
        return Response({"status": "ok", "service": "QuitoMove Smart Mobility"})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Registrar usuario",
        description="Crear una nueva cuenta. El usuario se asigna automáticamente al grupo 'User' y se crea su perfil.",
        tags=["Auth"],
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Usuario registrado correctamente",
                response=UserSerializer,
            ),
            400: OpenApiResponse(description="Error de validación — datos inválidos o usuario duplicado"),
        },
        examples=[
            OpenApiExample(
                name="Registro básico",
                value={"username": "nuevo_usuario", "password": "MiPassword123"},
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.REGISTER,
            detail=f"Registro de usuario: {user.username}",
        )
        return Response(
            {
                "success": True,
                "message": "Usuario registrado correctamente",
                "data": UserSerializer(user).data,
            },
            status=201,
        )


class LoginView(TokenObtainPairView):
    @extend_schema(
        summary="Iniciar sesión",
        description="Autenticar usuario y obtener tokens JWT (access + refresh). El access expira en 30 min, el refresh en 1 día.",
        tags=["Auth"],
        responses={
            200: OpenApiResponse(
                description="Tokens obtenidos correctamente",
                response={"type": "object", "properties": {
                    "access": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIs..."},
                    "refresh": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIs..."},
                }},
            ),
            401: OpenApiResponse(description="Credenciales inválidas"),
        },
        examples=[
            OpenApiExample(
                name="Login admin",
                value={"username": "admin", "password": "admin123"},
                request_only=True,
            ),
            OpenApiExample(
                name="Login conductor",
                value={"username": "conductor1", "password": "demo123"},
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            from django.contrib.auth import authenticate
            user = authenticate(
                request=request,
                username=request.data.get("username"),
                password=request.data.get("password"),
            )
            if user:
                AuditLog.objects.create(
                    user=user,
                    action=AuditLog.Action.LOGIN,
                    detail=f"Inicio de sesión: {user.username}",
                )
        return response


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Obtener perfil del usuario autenticado",
        description="Devuelve los datos del usuario actual, incluyendo grupos y perfil",
        tags=["Auth"],
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ProfileView(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

    @extend_schema(
        summary="Actualizar perfil",
        description="Actualizar los campos del perfil del usuario autenticado (avatar, dirección, contactos de emergencia)",
        tags=["Auth"],
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Cambiar contraseña",
        description="Cambiar la contraseña del usuario autenticado. Requiere la contraseña actual.",
        tags=["Auth"],
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Contraseña actualizada correctamente"),
            400: OpenApiResponse(description="Error de validación — contraseña actual incorrecta o nueva no cumple requisitos"),
        },
        examples=[
            OpenApiExample(
                name="Cambio de contraseña",
                value={"old_password": "MiPassword123", "new_password": "NuevaPassword456"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.PASSWORD_CHANGE,
            detail="Cambio de contraseña",
        )
        return Response(
            {"success": True, "message": "Contraseña actualizada correctamente"},
            status=status.HTTP_200_OK,
        )
