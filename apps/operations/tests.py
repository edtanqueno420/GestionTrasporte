from datetime import date, time

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.operations.models import (
    Driver,
    DriverAssignment,
    GPSPosition,
    Maintenance,
    RouteCoordinate,
    Schedule,
    Trip,
)
from apps.transport.models import BusStop, Route, Vehicle, VehicleType, VehicleStatus

# ----------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------


def _create_route(code="R-01", name="Ruta 1"):
    return Route.objects.create(code=code, name=name)


def _create_vehicle(plate="ABC-123", model_year=2020):
    vtype = VehicleType.objects.create(name="Bus", code="VT-BUS")
    vstatus = VehicleStatus.objects.create(name="Activo", code="VS-ACT")
    return Vehicle.objects.create(
        plate=plate, brand="Marca", model="Modelo",
        year=model_year, capacity=40, vehicle_type=vtype, vehicle_status=vstatus,
    )


def _create_driver(user, license_number="LIC-001"):
    return Driver.objects.create(
        user=user, license_number=license_number,
        license_type=Driver.LicenseType.C,
        hire_date=date(2023, 1, 15), experience_years=5,
    )


# ----------------------------------------------------------------
# Driver Tests
# ----------------------------------------------------------------

class DriverModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="driver", password="test",
            first_name="Juan", last_name="Pérez",
        )
        self.driver = _create_driver(self.user)

    def test_str(self):
        expected = "Juan Pérez (LIC-001)"
        self.assertEqual(str(self.driver), expected)

    def test_soft_delete(self):
        self.driver.delete()
        self.driver.refresh_from_db()
        self.assertFalse(self.driver.is_active)
        self.assertNotIn(self.driver, Driver.objects.all())
        self.assertIn(self.driver, Driver.all_objects.all())

    def test_ordering(self):
        u2 = User.objects.create_user(username="driver2", password="test")
        d2 = _create_driver(u2, license_number="LIC-002")
        qs = Driver.objects.all()
        self.assertEqual(qs.first(), d2)
        self.assertEqual(qs.last(), self.driver)


class DriverAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="dadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="duser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))
        cls.driver_user = User.objects.create_user(
            username="driver1", password="test",
            first_name="Ana", last_name="López",
        )

    def test_list_requires_auth(self):
        response = self.client.get("/api/operations/drivers/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/drivers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/drivers/",
            {"user": self.driver_user.id, "license_number": "LIC-999",
             "license_type": "C", "hire_date": "2023-01-15"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/drivers/",
            {"user": self.driver_user.id, "license_number": "LIC-ADM",
             "license_type": "C", "hire_date": "2023-01-15"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["license_number"], "LIC-ADM")

    def test_admin_can_delete_soft(self):
        d = Driver.objects.create(
            user=self.driver_user, license_number="LIC-DEL",
            license_type="C", hire_date=date(2023, 1, 15),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/operations/drivers/{d.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        d.refresh_from_db()
        self.assertFalse(d.is_active)

    def test_pagination(self):
        self.client.force_authenticate(user=self.admin)
        for i in range(25):
            u = User.objects.create_user(
                username=f"driver_bulk_{i}", password="test",
            )
            Driver.objects.create(
                user=u, license_number=f"LIC-BULK-{i:03d}",
                license_type="C", hire_date=date(2023, 1, 15),
            )
        response = self.client.get("/api/operations/drivers/")
        self.assertEqual(len(response.json()["results"]), 20)
        self.assertIsNotNone(response.json()["next"])

    def test_search_by_license(self):
        u = User.objects.create_user(username="dsearch", password="test")
        Driver.objects.create(
            user=u, license_number="LIC-SEARCH",
            license_type="C", hire_date=date(2023, 1, 15),
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/drivers/?search=SEARCH")
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_filter_by_available(self):
        self.client.force_authenticate(user=self.admin)
        Driver.objects.create(
            user=self.driver_user, license_number="LIC-AVAIL",
            license_type="C", hire_date=date(2023, 1, 15),
            is_available=True,
        )
        response = self.client.get("/api/operations/drivers/?is_available=true")
        self.assertGreaterEqual(len(response.json()["results"]), 1)


# ----------------------------------------------------------------
# DriverAssignment Tests
# ----------------------------------------------------------------

class DriverAssignmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dassign", password="test")
        self.driver = _create_driver(self.user)
        self.vehicle = _create_vehicle()
        self.assignment = DriverAssignment.objects.create(
            driver=self.driver, vehicle=self.vehicle,
            assignment_date=date(2023, 6, 1),
        )

    def test_str(self):
        expected = f"{self.driver} → {self.vehicle.plate} ({self.assignment.assignment_date})"
        self.assertEqual(str(self.assignment), expected)

    def test_soft_delete(self):
        self.assignment.delete()
        self.assignment.refresh_from_db()
        self.assertFalse(self.assignment.is_active)

    def test_unique_active_assignment(self):
        with self.assertRaises(Exception):
            DriverAssignment.objects.create(
                driver=self.driver, vehicle=self.vehicle,
                assignment_date=date(2023, 7, 1),
            )


class DriverAssignmentAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="daadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="dauser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))
        cls.driver_user = User.objects.create_user(
            username="dadriver", password="test",
        )
        cls.driver = _create_driver(cls.driver_user, license_number="LIC-DA")
        cls.vehicle = _create_vehicle(plate="DA-001")

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/driver-assignments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/driver-assignments/",
            {"driver": self.driver.id, "vehicle": self.vehicle.id,
             "assignment_date": "2023-06-01"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_active_assignment_validation(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/operations/driver-assignments/",
            {"driver": self.driver.id, "vehicle": self.vehicle.id,
             "assignment_date": "2023-06-01"},
            format="json",
        )
        response = self.client.post(
            "/api/operations/driver-assignments/",
            {"driver": self.driver.id, "vehicle": self.vehicle.id,
             "assignment_date": "2023-07-01"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/driver-assignments/",
            {"driver": self.driver.id, "vehicle": self.vehicle.id,
             "assignment_date": "2023-06-01"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ----------------------------------------------------------------
# Schedule Tests
# ----------------------------------------------------------------

class ScheduleModelTest(TestCase):
    def setUp(self):
        self.route = _create_route()
        self.schedule = Schedule.objects.create(
            route=self.route,
            departure_time=time(8, 0), arrival_time=time(9, 0),
            frequency_minutes=15, operating_days="12345",
        )

    def test_str(self):
        expected = f"{self.route.code} (08:00:00 - 09:00:00)"
        self.assertEqual(str(self.schedule), expected)

    def test_soft_delete(self):
        self.schedule.delete()
        self.schedule.refresh_from_db()
        self.assertFalse(self.schedule.is_active)

    def test_ordering(self):
        s2 = Schedule.objects.create(
            route=self.route,
            departure_time=time(7, 0), arrival_time=time(8, 0),
            frequency_minutes=10, operating_days="12345",
        )
        qs = Schedule.objects.all()
        self.assertEqual(qs.first(), s2)
        self.assertEqual(qs.last(), self.schedule)


class ScheduleAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="sadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="suser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))
        cls.route = _create_route(code="R-SCH", name="Ruta Schedule")

    def test_admin_can_create_schedule(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/schedules/",
            {"route": self.route.id, "departure_time": "07:00:00",
             "arrival_time": "08:00:00", "frequency_minutes": 15,
             "operating_days": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_departure_before_arrival_validation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/schedules/",
            {"route": self.route.id, "departure_time": "09:00:00",
             "arrival_time": "08:00:00", "frequency_minutes": 15,
             "operating_days": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/schedules/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/schedules/",
            {"route": self.route.id, "departure_time": "07:00:00",
             "arrival_time": "08:00:00", "frequency_minutes": 15,
             "operating_days": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ----------------------------------------------------------------
# RouteCoordinate Tests
# ----------------------------------------------------------------

class RouteCoordinateModelTest(TestCase):
    def setUp(self):
        self.route = _create_route()
        self.coord = RouteCoordinate.objects.create(
            route=self.route,
            latitude=-0.229498, longitude=-78.524277,
            order=1,
        )

    def test_str(self):
        expected = f"{self.route.code} - punto 1"
        self.assertEqual(str(self.coord), expected)

    def test_soft_delete(self):
        self.coord.delete()
        self.coord.refresh_from_db()
        self.assertFalse(self.coord.is_active)

    def test_unique_order_per_route(self):
        with self.assertRaises(Exception):
            RouteCoordinate.objects.create(
                route=self.route,
                latitude=-0.230000, longitude=-78.520000,
                order=1,
            )


class RouteCoordinateAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="rcadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="rcuser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))
        cls.route = _create_route(code="R-COORD", name="Ruta Coord")

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/route-coordinates/",
            {"route": self.route.id, "latitude": -0.229498,
             "longitude": -78.524277, "order": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_order_validation(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/operations/route-coordinates/",
            {"route": self.route.id, "latitude": -0.229498,
             "longitude": -78.524277, "order": 1},
            format="json",
        )
        response = self.client.post(
            "/api/operations/route-coordinates/",
            {"route": self.route.id, "latitude": -0.230000,
             "longitude": -78.520000, "order": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/route-coordinates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_delete_soft(self):
        coord = RouteCoordinate.objects.create(
            route=self.route,
            latitude=-0.229498, longitude=-78.524277, order=1,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/operations/route-coordinates/{coord.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        coord.refresh_from_db()
        self.assertFalse(coord.is_active)


# ----------------------------------------------------------------
# Maintenance Tests
# ----------------------------------------------------------------

class MaintenanceModelTest(TestCase):
    def setUp(self):
        self.vehicle = _create_vehicle()
        self.mt = Maintenance.objects.create(
            vehicle=self.vehicle,
            maintenance_type=Maintenance.MaintenanceType.PREVENTIVE,
            description="Cambio de aceite",
            scheduled_date=date(2024, 1, 15),
            status=Maintenance.Status.SCHEDULED,
        )

    def test_str(self):
        expected = f"{self.vehicle.plate} - Preventivo (Programado)"
        self.assertEqual(str(self.mt), expected)

    def test_soft_delete(self):
        self.mt.delete()
        self.mt.refresh_from_db()
        self.assertFalse(self.mt.is_active)

    def test_ordering(self):
        mt2 = Maintenance.objects.create(
            vehicle=self.vehicle,
            maintenance_type=Maintenance.MaintenanceType.CORRECTIVE,
            description="Frenos",
            scheduled_date=date(2024, 2, 1),
            status=Maintenance.Status.SCHEDULED,
        )
        qs = Maintenance.objects.all()
        self.assertEqual(qs.first(), mt2)


class MaintenanceAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="mtadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="mtuser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))
        cls.vehicle = _create_vehicle(plate="MT-001")

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/maintenances/",
            {"vehicle": self.vehicle.id,
             "maintenance_type": "preventive",
             "description": "Cambio aceite",
             "scheduled_date": "2024-01-15"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "scheduled")

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/maintenances/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/maintenances/",
            {"vehicle": self.vehicle.id,
             "maintenance_type": "preventive",
             "description": "Test", "scheduled_date": "2024-01-15"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_completed_requires_date_validation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/maintenances/",
            {"vehicle": self.vehicle.id,
             "maintenance_type": "preventive",
             "description": "Test",
             "scheduled_date": "2024-01-15",
             "status": "completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_completed_date_not_before_scheduled(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/maintenances/",
            {"vehicle": self.vehicle.id,
             "maintenance_type": "preventive",
             "description": "Test",
             "scheduled_date": "2024-01-20",
             "completed_date": "2024-01-15",
             "status": "completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.admin)
        Maintenance.objects.create(
            vehicle=self.vehicle,
            maintenance_type=Maintenance.MaintenanceType.PREVENTIVE,
            description="Test", scheduled_date=date(2024, 1, 15),
            status=Maintenance.Status.SCHEDULED,
        )
        response = self.client.get(
            "/api/operations/maintenances/?status=scheduled"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_filter_by_type(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            "/api/operations/maintenances/?maintenance_type=preventive"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ----------------------------------------------------------------
# Trip Tests
# ----------------------------------------------------------------

class TripModelTest(TestCase):
    def setUp(self):
        self.route = _create_route(code="R-TRIP", name="Ruta Trip")
        self.vehicle = _create_vehicle(plate="TRP-001")
        self.user = User.objects.create_user(username="tdriver", password="test")
        self.driver = _create_driver(self.user, license_number="LIC-TRP")
        self.schedule = Schedule.objects.create(
            route=self.route,
            departure_time=time(8, 0), arrival_time=time(9, 0),
            frequency_minutes=15, operating_days="12345",
        )
        self.trip = Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
            arrival_datetime="2024-06-01T09:30:00Z",
            status=Trip.Status.COMPLETED,
            passenger_count=30,
        )

    def test_str(self):
        expected = (f"{self.route.code} - {self.vehicle.plate} "
                    f"({self.trip.trip_date} {self.trip.departure_datetime})")
        self.assertEqual(str(self.trip), expected)

    def test_soft_delete(self):
        self.trip.delete()
        self.trip.refresh_from_db()
        self.assertFalse(self.trip.is_active)
        self.assertNotIn(self.trip, Trip.objects.all())
        self.assertIn(self.trip, Trip.all_objects.all())

    def test_ordering(self):
        t2 = Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 7, 1),
            departure_datetime="2024-07-01T08:00:00Z",
            status=Trip.Status.SCHEDULED,
        )
        qs = Trip.objects.all()
        self.assertEqual(qs.first(), t2)


class TripAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="tadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="tuser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))

    def setUp(self):
        self.route = _create_route(code="R-TRP-API", name="Ruta API Trip")
        self.vehicle = _create_vehicle(plate="TRP-API")
        self.user = User.objects.create_user(username="tripdriver", password="test")
        self.driver = _create_driver(self.user, license_number="LIC-TRP-API")
        self.schedule = Schedule.objects.create(
            route=self.route,
            departure_time=time(8, 0), arrival_time=time(9, 0),
            frequency_minutes=15, operating_days="12345",
        )

    def test_list_requires_auth(self):
        response = self.client.get("/api/operations/trips/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/trips/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/trips/",
            {"route": self.route.id, "vehicle": self.vehicle.id,
             "driver": self.driver.id, "schedule": self.schedule.id,
             "trip_date": "2024-06-01",
             "departure_datetime": "2024-06-01T08:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/trips/",
            {"route": self.route.id, "vehicle": self.vehicle.id,
             "driver": self.driver.id, "schedule": self.schedule.id,
             "trip_date": "2024-06-01",
             "departure_datetime": "2024-06-01T08:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_delete_soft(self):
        t = Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/operations/trips/{t.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        t.refresh_from_db()
        self.assertFalse(t.is_active)

    def test_departure_before_arrival_validation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/trips/",
            {"route": self.route.id, "vehicle": self.vehicle.id,
             "driver": self.driver.id, "schedule": self.schedule.id,
             "trip_date": "2024-06-01",
             "departure_datetime": "2024-06-01T10:00:00Z",
             "arrival_datetime": "2024-06-01T09:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_schedule_belongs_to_route_validation(self):
        other_route = _create_route(code="R-OTHER", name="Otra Ruta")
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/trips/",
            {"route": other_route.id, "vehicle": self.vehicle.id,
             "driver": self.driver.id, "schedule": self.schedule.id,
             "trip_date": "2024-06-01",
             "departure_datetime": "2024-06-01T08:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_status(self):
        Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
            status=Trip.Status.COMPLETED,
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            "/api/operations/trips/?status=completed"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_filter_by_route(self):
        Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            f"/api/operations/trips/?route={self.route.id}"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_search(self):
        Trip.objects.create(
            route=self.route, vehicle=self.vehicle,
            driver=self.driver, schedule=self.schedule,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            f"/api/operations/trips/?search={self.vehicle.plate}"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)


# ----------------------------------------------------------------
# GPSPosition Tests
# ----------------------------------------------------------------

class GPSPositionModelTest(TestCase):
    def setUp(self):
        route = _create_route(code="R-GPS", name="Ruta GPS")
        vehicle = _create_vehicle(plate="GPS-001")
        user = User.objects.create_user(username="gpsdriver", password="test")
        driver = _create_driver(user, license_number="LIC-GPS")
        self.trip = Trip.objects.create(
            route=route, vehicle=vehicle, driver=driver,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
        )
        self.pos = GPSPosition.objects.create(
            trip=self.trip,
            latitude=-0.229498, longitude=-78.524277,
            speed=35.5, heading=180.0,
            recorded_at="2024-06-01T08:15:00Z",
        )

    def test_str(self):
        expected = f"{self.trip} - (-0.229498, -78.524277) @ {self.pos.recorded_at}"
        self.assertEqual(str(self.pos), expected)

    def test_soft_delete(self):
        self.pos.delete()
        self.pos.refresh_from_db()
        self.assertFalse(self.pos.is_active)
        self.assertNotIn(self.pos, GPSPosition.objects.all())
        self.assertIn(self.pos, GPSPosition.all_objects.all())


class GPSPositionAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="gadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="guser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))

    def setUp(self):
        route = _create_route(code="R-GPS-API", name="Ruta GPS API")
        vehicle = _create_vehicle(plate="GPS-API")
        user = User.objects.create_user(username="gpsapidriver", password="test")
        driver = _create_driver(user, license_number="LIC-GPS-API")
        self.trip = Trip.objects.create(
            route=route, vehicle=vehicle, driver=driver,
            trip_date=date(2024, 6, 1),
            departure_datetime="2024-06-01T08:00:00Z",
        )

    def test_list_requires_auth(self):
        response = self.client.get("/api/operations/gps-positions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/operations/gps-positions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/operations/gps-positions/",
            {"trip": self.trip.id, "latitude": -0.229498,
             "longitude": -78.524277,
             "recorded_at": "2024-06-01T08:15:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/gps-positions/",
            {"trip": self.trip.id, "latitude": -0.229498,
             "longitude": -78.524277,
             "recorded_at": "2024-06-01T08:15:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_delete_soft(self):
        pos = GPSPosition.objects.create(
            trip=self.trip,
            latitude=-0.229498, longitude=-78.524277,
            recorded_at="2024-06-01T08:15:00Z",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/operations/gps-positions/{pos.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        pos.refresh_from_db()
        self.assertFalse(pos.is_active)

    def test_invalid_latitude_validation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/gps-positions/",
            {"trip": self.trip.id, "latitude": 100,
             "longitude": -78.524277,
             "recorded_at": "2024-06-01T08:15:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_longitude_validation(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/operations/gps-positions/",
            {"trip": self.trip.id, "latitude": -0.229498,
             "longitude": 200,
             "recorded_at": "2024-06-01T08:15:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_trip(self):
        GPSPosition.objects.create(
            trip=self.trip,
            latitude=-0.229498, longitude=-78.524277,
            recorded_at="2024-06-01T08:15:00Z",
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            f"/api/operations/gps-positions/?trip={self.trip.id}"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_filter_by_date_range(self):
        GPSPosition.objects.create(
            trip=self.trip,
            latitude=-0.229498, longitude=-78.524277,
            recorded_at="2024-06-01T08:00:00Z",
        )
        GPSPosition.objects.create(
            trip=self.trip,
            latitude=-0.230000, longitude=-78.520000,
            recorded_at="2024-06-01T10:00:00Z",
        )
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            "/api/operations/gps-positions/"
            "?recorded_at_after=2024-06-01T09:00:00Z"
        )
        self.assertEqual(len(response.json()["results"]), 1)
