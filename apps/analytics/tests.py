from datetime import UTC, date, datetime, timedelta

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentType
from apps.operations.models import Driver, GPSPosition, RouteCoordinate, Schedule, Trip
from apps.transport.models import BusStop, Route, RouteBusStop, Vehicle


class DashboardTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")

    def setUp(self):
        user = User.objects.create_user(username="analyticsuser", password="testpass123")
        user.groups.add(Group.objects.get(name="User"))
        self.client.force_authenticate(user=user)

    def test_dashboard_returns_200(self):
        response = self.client.get("/api/analytics/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("total_trips_today", data)
        self.assertIn("active_vehicles", data)
        self.assertIn("total_incidents_open", data)
        self.assertIn("average_trip_duration_minutes", data)
        self.assertIn("punctuality_rate", data)

    def test_dashboard_requires_auth(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/analytics/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RouteReportTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.route = Route.objects.create(name="Ruta Test", code="RT-TST")
        cls.user = User.objects.create_user(username="routetest", password="testpass123")
        cls.user.groups.add(Group.objects.get(name="User"))
        vehicle = Vehicle.objects.create(plate="RPT-001", capacity=50, year=2020)
        driver_user = User.objects.create_user(username="driver_rpt", password="testpass123")
        driver = Driver.objects.create(
            user=driver_user, license_number="LIC-RPT", hire_date=date(2020, 1, 1),
        )
        Trip.objects.create(
            route=cls.route, vehicle=vehicle, driver=driver,
            trip_date=date.today(),
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
            arrival_datetime=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            status=Trip.Status.COMPLETED,
        )

    def test_route_report_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/routes/{self.route.id}/report/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["route_id"], self.route.id)
        self.assertEqual(data["total_trips"], 1)

    def test_route_report_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/routes/999/report/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VehicleReportTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.vehicle = Vehicle.objects.create(plate="VHC-RPT", capacity=50, year=2020)
        cls.user = User.objects.create_user(username="vhctest", password="testpass123")
        cls.user.groups.add(Group.objects.get(name="User"))

    def test_vehicle_report_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/analytics/vehicles/{self.vehicle.id}/report/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["vehicle_id"], self.vehicle.id)
        self.assertIn("estimated_km", data)

    def test_vehicle_report_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/analytics/vehicles/999/report/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SystemStatusTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")

    def test_status_is_public(self):
        response = self.client.get("/api/analytics/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "operational")
        self.assertIn("active_routes", data)
        self.assertIn("active_vehicles", data)
        self.assertIn("open_incidents", data)


class PublicRoutesTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Route.objects.create(name="Ruta Publica", code="RT-PUB")

    def test_public_routes_no_auth(self):
        response = self.client.get("/api/public/routes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_public_bus_stops_no_auth(self):
        response = self.client.get("/api/public/bus-stops/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_route_stops_no_auth(self):
        route = Route.objects.first()
        response = self.client.get(f"/api/public/routes/{route.id}/stops/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_route_coordinates_no_auth(self):
        route = Route.objects.first()
        response = self.client.get(f"/api/public/routes/{route.id}/coordinates/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_route_coordinates_ordered(self):
        route = Route.objects.first()
        RouteCoordinate.objects.create(route=route, latitude=0, longitude=0, order=2)
        RouteCoordinate.objects.create(route=route, latitude=1, longitude=1, order=1)
        response = self.client.get(f"/api/public/routes/{route.id}/coordinates/")
        data = response.json()
        self.assertEqual(data[0]["order"], 1)
        self.assertEqual(data[1]["order"], 2)

    def test_public_route_stops_ordered(self):
        route = Route.objects.first()
        bs1 = BusStop.objects.create(code="BS-A", name="A", latitude=0, longitude=0)
        bs2 = BusStop.objects.create(code="BS-B", name="B", latitude=1, longitude=1)
        RouteBusStop.objects.create(route=route, bus_stop=bs2, stop_order=2)
        RouteBusStop.objects.create(route=route, bus_stop=bs1, stop_order=1)
        response = self.client.get(f"/api/public/routes/{route.id}/stops/")
        data = response.json()
        self.assertEqual(data[0]["stop_order"], 1)
        self.assertEqual(data[1]["stop_order"], 2)


class GPSFilterTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.user = User.objects.create_user(username="gpstest", password="testpass123")
        cls.user.groups.add(Group.objects.get(name="User"))
        route = Route.objects.create(name="GPS Ruta", code="RT-GPS")
        vehicle = Vehicle.objects.create(plate="GPS-001", capacity=50, year=2020)
        driver_user = User.objects.create_user(username="driver_gps", password="testpass123")
        driver = Driver.objects.create(
            user=driver_user, license_number="LIC-GPS", hire_date=date(2020, 1, 1),
        )
        cls.trip = Trip.objects.create(
            route=route, vehicle=vehicle, driver=driver,
            trip_date=date.today(),
            departure_datetime=datetime(2026, 6, 1, 8, 0, tzinfo=UTC),
        )

    def test_gps_filter_by_trip(self):
        GPSPosition.objects.create(
            trip=self.trip, latitude=0, longitude=0,
            recorded_at=datetime(2026, 6, 1, 8, 30, tzinfo=UTC),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/operations/gps-positions/?trip={self.trip.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_gps_filter_by_date_range(self):
        GPSPosition.objects.create(
            trip=self.trip, latitude=0, longitude=0,
            recorded_at=datetime(2026, 6, 1, 8, 30, tzinfo=UTC),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/operations/gps-positions/"
            "?recorded_at_after=2026-06-01T08:00:00Z"
            "&recorded_at_before=2026-06-01T09:00:00Z"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)


class RouteCoordinateOrderTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.user = User.objects.create_user(username="coords", password="testpass123")
        cls.user.groups.add(Group.objects.get(name="User"))
        cls.route = Route.objects.create(name="Coord Route", code="RT-CRD")

    def test_route_coordinates_ordered_by_order(self):
        RouteCoordinate.objects.create(route=self.route, latitude=0, longitude=0, order=3)
        RouteCoordinate.objects.create(route=self.route, latitude=1, longitude=1, order=1)
        RouteCoordinate.objects.create(route=self.route, latitude=2, longitude=2, order=2)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/operations/route-coordinates/?route={self.route.id}"
        )
        data = response.json()["results"]
        self.assertEqual(data[0]["order"], 1)
        self.assertEqual(data[1]["order"], 2)
        self.assertEqual(data[2]["order"], 3)

    def test_public_route_stops_ordered(self):
        bs1 = BusStop.objects.create(code="CRD-A", name="A", latitude=0, longitude=0)
        bs2 = BusStop.objects.create(code="CRD-B", name="B", latitude=1, longitude=1)
        RouteBusStop.objects.create(route=self.route, bus_stop=bs2, stop_order=2)
        RouteBusStop.objects.create(route=self.route, bus_stop=bs1, stop_order=1)
        response = self.client.get(f"/api/public/routes/{self.route.id}/stops/")
        data = response.json()
        self.assertEqual(data[0]["stop_order"], 1)
        self.assertEqual(data[1]["stop_order"], 2)
