from datetime import UTC, datetime, timedelta

from apps.accounts.models import User
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.incidents.models import Incident, IncidentType
from apps.operations.models import Driver, Trip
from apps.transport.models import Route, Vehicle


class IncidentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        incident_type = IncidentType.objects.create(name="Accidente", code="IT-ACC")
        route = Route.objects.create(name="Ruta A", code="RT-A")
        cls.vehicle = Vehicle.objects.create(plate="ABC-1234", capacity=50, year=2020)
        driver_user = User.objects.create_user(username="driver1", password="testpass123")
        cls.driver = Driver.objects.create(
            user=driver_user, license_number="LIC-001",
            hire_date=datetime(2020, 1, 1).date(),
        )
        cls.trip = Trip.objects.create(
            route=route, vehicle=cls.vehicle, driver=cls.driver,
            trip_date=datetime(2026, 6, 1).date(),
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            arrival_datetime=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        )
        cls.incident = Incident.objects.create(
            trip=cls.trip, incident_type=incident_type,
            vehicle=cls.vehicle, latitude=-0.22985, longitude=-78.52495,
            severity=Incident.Severity.HIGH,
        )

    def test_str(self):
        expected = f"Alta - Accidente ({self.trip})"
        self.assertEqual(str(self.incident), expected)

    def test_default_status(self):
        self.assertEqual(self.incident.status, Incident.Status.OPEN)

    def test_soft_delete(self):
        self.incident.delete()
        self.incident.refresh_from_db()
        self.assertFalse(self.incident.is_active)
        self.assertNotIn(self.incident, Incident.objects.all())
        self.assertIn(self.incident, Incident.all_objects.all())

    def test_ordering(self):
        b = Incident.objects.create(
            trip=self.trip, incident_type=self.incident.incident_type,
            vehicle=self.vehicle, latitude=0, longitude=0,
        )
        qs = Incident.objects.all()
        self.assertEqual(qs.first(), b)

    def test_invalid_latitude(self):
        with self.assertRaises(Exception):
            inc = Incident(
                trip=self.trip, incident_type=self.incident.incident_type,
                vehicle=self.vehicle, latitude=100, longitude=0,
            )
            inc.full_clean()


class IncidentAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        admin_group = Group.objects.get(name="Administrator")
        user_group = Group.objects.get(name="User")

        cls.admin = cls._create_user("incadmin", admin_group)
        cls.regular = cls._create_user("incuser", user_group)

        cls.incident_type = IncidentType.objects.create(name="Accidente", code="IT-ACC")
        route = Route.objects.create(name="Ruta A", code="RT-A")
        cls.vehicle = Vehicle.objects.create(plate="ABC-1234", capacity=50, year=2020)
        driver_user = User.objects.create_user(username="driver2", password="testpass123")
        cls.driver = Driver.objects.create(
            user=driver_user, license_number="LIC-002",
            hire_date=datetime(2020, 1, 1).date(),
        )
        cls.trip = Trip.objects.create(
            route=route, vehicle=cls.vehicle, driver=cls.driver,
            trip_date=datetime(2026, 6, 1).date(),
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            arrival_datetime=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        )

    @staticmethod
    def _create_user(username, group):
        user = User.objects.create_user(username=username, password="testpass123")
        user.groups.add(group)
        return user

    def _incident_data(self, **kwargs):
        data = {
            "trip": self.trip.id,
            "incident_type": self.incident_type.id,
            "latitude": -0.22985,
            "longitude": -78.52495,
        }
        data.update(kwargs)
        return data

    def test_list_requires_auth(self):
        response = self.client.get("/api/incidents/incidents/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/incidents/incidents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/incidents/incidents/",
            self._incident_data(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/incidents/incidents/",
            self._incident_data(),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_delete_soft(self):
        inc = Incident.objects.create(
            trip=self.trip, incident_type=self.incident_type,
            vehicle=self.vehicle, latitude=0, longitude=0,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/incidents/incidents/{inc.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        inc.refresh_from_db()
        self.assertFalse(inc.is_active)

    def test_date_range_filter(self):
        Incident.objects.create(
            trip=self.trip, incident_type=self.incident_type,
            vehicle=self.vehicle, latitude=0, longitude=0,
        )
        self.client.force_authenticate(user=self.regular)
        future = datetime(2099, 1, 1, tzinfo=UTC)
        encoded = future.isoformat().replace("+", "%2B")
        response = self.client.get(
            f"/api/incidents/incidents/?created_at_after={encoded}"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 0)

    def test_admin_can_resolve(self):
        inc = Incident.objects.create(
            trip=self.trip, incident_type=self.incident_type,
            vehicle=self.vehicle, latitude=0, longitude=0,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f"/api/incidents/incidents/{inc.id}/resolve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inc.refresh_from_db()
        self.assertEqual(inc.status, Incident.Status.RESOLVED)
        self.assertIsNotNone(inc.resolved_at)

    def test_invalid_coordinates_serializer(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/incidents/incidents/",
            self._incident_data(latitude=100, longitude=0),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_search(self):
        default_tz = datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
        route = Route.objects.create(name="Ruta XYZ", code="RT-XYZ")
        driver_user = User.objects.create_user(username="driver3", password="testpass123")
        driver2 = Driver.objects.create(
            user=driver_user, license_number="LIC-003",
            hire_date=datetime(2020, 1, 1).date(),
        )
        trip2 = Trip.objects.create(
            route=route, vehicle=self.vehicle, driver=driver2,
            trip_date=datetime(2026, 6, 1).date(),
            departure_datetime=default_tz, arrival_datetime=default_tz + timedelta(hours=2),
        )
        Incident.objects.create(
            trip=trip2, incident_type=self.incident_type,
            vehicle=self.vehicle, latitude=0, longitude=0,
            description="Freno roto",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/incidents/incidents/?search=Freno")
        self.assertEqual(len(response.json()["results"]), 1)


class IncidentSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        admin_group = Group.objects.get(name="Administrator")
        cls.admin = User.objects.create_user(username="notifyadmin", password="testpass123")
        cls.admin.groups.add(admin_group)

        incident_type = IncidentType.objects.create(name="Accidente", code="IT-SIG")
        route = Route.objects.create(name="Ruta Signal", code="RT-SIG")
        vehicle = Vehicle.objects.create(plate="SIGN-01", capacity=50, year=2020)
        driver_user = User.objects.create_user(username="driver_sig", password="testpass123")
        driver = Driver.objects.create(
            user=driver_user, license_number="LIC-SIG",
            hire_date=datetime(2020, 1, 1).date(),
        )
        cls.trip = Trip.objects.create(
            route=route, vehicle=vehicle, driver=driver,
            trip_date=datetime(2026, 6, 1).date(),
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            arrival_datetime=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        )
        cls.incident_type = incident_type

    def test_incident_creates_notification_for_admins(self):
        from apps.notifications.models import Notification
        Incident.objects.create(
            trip=self.trip, incident_type=self.incident_type,
            latitude=0, longitude=0,
        )
        self.assertEqual(Notification.objects.filter(user=self.admin).count(), 1)
        notification = Notification.objects.get(user=self.admin)
        self.assertEqual(notification.type, Notification.Type.INCIDENT)
        self.assertIn("Accidente", notification.title)

    def test_no_notification_for_regular_users(self):
        from apps.notifications.models import Notification
        regular = User.objects.create_user(username="regular_sig", password="testpass123")
        regular.groups.add(Group.objects.get(name="User"))
        Incident.objects.create(
            trip=self.trip, incident_type=self.incident_type,
            latitude=0, longitude=0,
        )
        self.assertEqual(Notification.objects.filter(user=regular).count(), 0)
