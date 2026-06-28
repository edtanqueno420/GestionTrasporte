from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import AuditLog, Profile, User


class HealthCheckTest(TestCase):
    def test_health_endpoint_returns_ok(self):
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class RegisterTest(TestCase):
    def test_register_creates_user_and_assigns_group(self):
        url = reverse("register")
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["message"], "Usuario registrado correctamente")
        user_groups = response.json()["data"]["groups"]
        self.assertIn("User", user_groups)

    def test_register_creates_profile(self):
        url = reverse("register")
        data = {
            "username": "profilestest",
            "email": "profile@test.com",
            "password": "testpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        user_id = response.json()["data"]["id"]
        self.assertTrue(Profile.objects.filter(user_id=user_id).exists())

    def test_register_creates_audit_log(self):
        url = reverse("register")
        data = {
            "username": "audittest",
            "email": "audit@test.com",
            "password": "testpass123",
        }
        self.client.post(url, data, format="json")
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.REGISTER
            ).exists()
        )


class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="logintest",
            password="testpass123",
        )

    def test_login_returns_tokens(self):
        url = reverse("token-obtain")
        response = self.client.post(url, {
            "username": "logintest",
            "password": "testpass123",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_login_creates_audit_log(self):
        url = reverse("token-obtain")
        self.client.post(url, {
            "username": "logintest",
            "password": "testpass123",
        }, format="json")
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.LOGIN,
                user=self.user,
            ).exists()
        )


class MeEndpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="metest", password="testpass123",
        )
        self.url = reverse("me")

    def _auth(self):
        token_url = reverse("token-obtain")
        response = self.client.post(token_url, {
            "username": "metest", "password": "testpass123",
        }, format="json")
        return response.json()["access"]

    def test_me_returns_user_data(self):
        token = self._auth()
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "metest")
        self.assertIn("profile", response.json())
        self.assertIn("groups", response.json())

    def test_me_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class ProfileEndpointTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="proftest", password="testpass123",
        )
        Profile.objects.get_or_create(user=self.user)

    def _auth(self):
        token_url = reverse("token-obtain")
        response = self.client.post(token_url, {
            "username": "proftest", "password": "testpass123",
        }, format="json")
        return response.json()["access"]

    def test_patch_profile(self):
        token = self._auth()
        url = reverse("profile")
        response = self.client.patch(
            url,
            {"address": "Quito, Ecuador"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["address"], "Quito, Ecuador")

    def test_profile_requires_auth(self):
        url = reverse("profile")
        response = self.client.patch(url, {"address": "test"}, content_type="application/json")
        self.assertEqual(response.status_code, 401)


class ChangePasswordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="changepasstest", password="oldpass123",
        )

    def _auth(self):
        token_url = reverse("token-obtain")
        response = self.client.post(token_url, {
            "username": "changepasstest", "password": "oldpass123",
        }, format="json")
        return response.json()["access"]

    def test_change_password_success(self):
        token = self._auth()
        url = reverse("change-password")
        response = self.client.post(
            url,
            {"old_password": "oldpass123", "new_password": "newpass123"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_change_password_invalid_old(self):
        token = self._auth()
        url = reverse("change-password")
        response = self.client.post(
            url,
            {"old_password": "wrongpass", "new_password": "newpass123"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_creates_audit_log(self):
        token = self._auth()
        url = reverse("change-password")
        self.client.post(
            url,
            {"old_password": "oldpass123", "new_password": "newpass456"},
            HTTP_AUTHORIZATION=f"Bearer {token}",
            content_type="application/json",
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.PASSWORD_CHANGE,
                user=self.user,
            ).exists()
        )

    def test_change_password_requires_auth(self):
        url = reverse("change-password")
        response = self.client.post(
            url,
            {"old_password": "x", "new_password": "y"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)


class PermissionsTest(TestCase):
    def test_register_endpoint_is_public(self):
        url = reverse("register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_health_endpoint_is_public(self):
        url = reverse("health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_login_endpoint_is_public(self):
        url = reverse("token-obtain")
        response = self.client.post(url, {}, format="json")
        self.assertNotEqual(response.status_code, 401)


class AuditLogModelTest(TestCase):
    def test_audit_log_str(self):
        user = User.objects.create_user(
            username="auditstr", password="testpass123",
        )
        log = AuditLog.objects.create(
            user=user,
            action=AuditLog.Action.LOGIN,
        )
        self.assertIn(str(user), str(log))
        self.assertIn("Inicio de sesión", str(log))


class ProfileModelTest(TestCase):
    def test_profile_auto_created(self):
        user = User.objects.create_user(
            username="autoprofile", password="testpass123",
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str(self):
        user = User.objects.create_user(
            username="profilestr", password="testpass123",
        )
        self.assertIn("profilestr", str(user.profile))
