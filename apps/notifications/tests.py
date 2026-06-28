from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.notifications.models import Notification, UserNotificationPreference


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test",
            message="Mensaje de prueba",
            type=Notification.Type.SYSTEM,
        )

    def test_str(self):
        expected = f"[Sistema] Test - {self.user}"
        self.assertEqual(str(self.notification), expected)

    def test_default_is_read(self):
        self.assertFalse(self.notification.is_read)

    def test_ordering(self):
        n2 = Notification.objects.create(
            user=self.user, title="B", message="Msg",
        )
        qs = Notification.objects.all()
        self.assertEqual(qs.first(), n2)

    def test_user_preference_auto_create(self):
        preference = UserNotificationPreference.objects.create(user=self.user)
        self.assertTrue(preference.email_enabled)
        self.assertTrue(preference.push_enabled)
        self.assertFalse(preference.sms_enabled)


class NotificationAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        admin_group = Group.objects.get(name="Administrator")
        user_group = Group.objects.get(name="User")

        cls.admin = User.objects.create_user(
            username="notifadmin", password="testpass123",
        )
        cls.admin.groups.add(admin_group)

        cls.user1 = User.objects.create_user(
            username="user1", password="testpass123",
        )
        cls.user1.groups.add(user_group)

        cls.user2 = User.objects.create_user(
            username="user2", password="testpass123",
        )
        cls.user2.groups.add(user_group)

    def _create_notification(self, user, **kwargs):
        data = dict(title="Incidente", message="Algo ocurrió", type=Notification.Type.INCIDENT)
        data.update(kwargs)
        return Notification.objects.create(user=user, **data)

    def test_list_requires_auth(self):
        response = self.client.get("/api/notifications/notifications/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own(self):
        self._create_notification(self.user1)
        self._create_notification(self.user2)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/notifications/")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_admin_sees_all(self):
        self._create_notification(self.user1)
        self._create_notification(self.user2)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/notifications/notifications/")
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

    def test_mark_as_read(self):
        n = self._create_notification(self.user1)
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(f"/api/notifications/notifications/{n.id}/read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_user_cannot_delete_own(self):
        n = self._create_notification(self.user1)
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f"/api/notifications/notifications/{n.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete(self):
        n = self._create_notification(self.user1)
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/notifications/notifications/{n.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_read_all(self):
        self._create_notification(self.user1)
        self._create_notification(self.user1)
        self.client.force_authenticate(user=self.user1)
        response = self.client.put("/api/notifications/notifications/read_all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.filter(user=self.user1, is_read=False).count(), 0,
        )

    def test_unread_count_in_list(self):
        self._create_notification(self.user1)
        self._create_notification(self.user1)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/notifications/")
        self.assertIn("unread_count", response.json())
        self.assertEqual(response.json()["unread_count"], 2)

    def test_filter_by_type(self):
        self._create_notification(self.user1, type=Notification.Type.INCIDENT)
        self._create_notification(self.user1, type=Notification.Type.SYSTEM)
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            "/api/notifications/notifications/?type=system"
        )
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
