from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import AuditLog, Profile, User
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserLocationSerializer,
    UserSerializer,
)
from apps.accounts.services.email import send_password_reset_email


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
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="Iniciar sesión",
        description="Autenticar usuario y obtener tokens JWT (access + refresh). Acepta username o email. El access expira en 30 min, el refresh en 1 día.",
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
                name="Login con username",
                value={"username": "admin", "password": "admin123"},
                request_only=True,
            ),
            OpenApiExample(
                name="Login con email",
                value={"email": "admin@test.com", "password": "admin123"},
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = authenticate(
                request=request,
                username=request.data.get("username") or request.data.get("email"),
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


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Solicitar reset de contraseña",
        description="Envía un correo con enlace de recuperación. Siempre responde 200 para evitar enumeración de usuarios.",
        tags=["Auth"],
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description="Correo enviado si el email está registrado")},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_password_reset_email(user, uid, token)
        except User.DoesNotExist:
            pass

        return Response(
            {"detail": "Si el correo está registrado, recibirás un enlace de recuperación."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Confirmar reset de contraseña",
        description="Valida el token y actualiza la contraseña. El token queda inválido tras el primer uso.",
        tags=["Auth"],
        request=PasswordResetConfirmSerializer,
        responses={200: OpenApiResponse(description="Contraseña actualizada correctamente")},
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )


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


class UserLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Actualizar ubicación del usuario",
        description="Actualiza la última ubicación conocida del usuario autenticado. La app móvil debe llamar a este endpoint periódicamente con la posición GPS del dispositivo.",
        tags=["Auth"],
        request=UserLocationSerializer,
        responses={
            200: OpenApiResponse(
                description="Ubicación actualizada correctamente",
                response={"type": "object", "properties": {
                    "success": {"type": "boolean", "example": True},
                    "latitude": {"type": "string", "example": "-0.180700"},
                    "longitude": {"type": "string", "example": "-78.467800"},
                }},
            ),
        },
        examples=[
            OpenApiExample(
                name="Actualizar ubicación",
                value={"latitude": -0.1807, "longitude": -78.4678},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = UserLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {
                "success": True,
                "latitude": str(serializer.validated_data["latitude"]),
                "longitude": str(serializer.validated_data["longitude"]),
            },
            status=status.HTTP_200_OK,
        )
