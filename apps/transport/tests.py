from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.transport.models import (
    BusStop,
    District,
    Route,
    RouteBusStop,
    Sector,
    TransportCompany,
    Vehicle,
    VehicleStatus,
    VehicleType,
)


class RouteSoftDeleteTest(TestCase):
    def setUp(self):
        self.route = Route.objects.create(
            code="R-SD-TEST",
            name="Ruta Soft Delete Test",
        )

    def test_delete_marks_as_inactive(self):
        self.route.delete()
        self.route.refresh_from_db()
        self.assertFalse(self.route.is_active)

    def test_delete_removes_from_default_manager(self):
        self.route.delete()
        self.assertNotIn(self.route, Route.objects.all())

    def test_delete_preserves_in_all_objects(self):
        self.route.delete()
        self.assertIn(self.route, Route.all_objects.all())

    def test_all_objects_includes_inactive(self):
        self.route.delete()
        self.assertEqual(Route.all_objects.count(), 1)


class BusStopSoftDeleteTest(TestCase):
    def setUp(self):
        self.stop = BusStop.objects.create(
            code="BS-SD-TEST",
            name="Parada Soft Delete Test",
            latitude=-0.229498,
            longitude=-78.524277,
        )

    def test_delete_marks_as_inactive(self):
        self.stop.delete()
        self.stop.refresh_from_db()
        self.assertFalse(self.stop.is_active)

    def test_delete_removes_from_default_manager(self):
        self.stop.delete()
        self.assertNotIn(self.stop, BusStop.objects.all())

    def test_delete_preserves_in_all_objects(self):
        self.stop.delete()
        self.assertIn(self.stop, BusStop.all_objects.all())


class VehicleSoftDeleteTest(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            plate="SD-TEST",
            brand="Test",
            model="Test Model",
            year=2024,
            capacity=50,
        )

    def test_delete_marks_as_inactive(self):
        self.vehicle.delete()
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.is_active)

    def test_delete_removes_from_default_manager(self):
        self.vehicle.delete()
        self.assertNotIn(self.vehicle, Vehicle.objects.all())

    def test_delete_preserves_in_all_objects(self):
        self.vehicle.delete()
        self.assertIn(self.vehicle, Vehicle.all_objects.all())


class DefaultManagerFilterTest(TestCase):
    def setUp(self):
        self.active = Route.objects.create(code="R-ACTIVE", name="Activa")
        self.inactive_route = Route.objects.create(
            code="R-INACTIVE", name="Inactiva",
        )
        self.inactive_route.delete()

    def test_objects_returns_only_active(self):
        qs = Route.objects.all()
        self.assertIn(self.active, qs)
        self.assertNotIn(self.inactive_route, qs)
        self.assertEqual(qs.count(), 1)

    def test_all_objects_returns_all(self):
        self.assertEqual(Route.all_objects.count(), 2)

    def test_queryset_delete_bulk(self):
        Route.objects.create(code="R-BULK1", name="Bulk 1")
        Route.objects.create(code="R-BULK2", name="Bulk 2")
        Route.objects.filter(code__startswith="R-BULK").delete()
        self.assertEqual(Route.objects.filter(code__startswith="R-BULK").count(), 0)
        self.assertEqual(
            Route.all_objects.filter(code__startswith="R-BULK").count(), 2,
        )
        for r in Route.all_objects.filter(code__startswith="R-BULK"):
            self.assertFalse(r.is_active)


class APISoftDeleteTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="sdadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))

    def setUp(self):
        self.route = Route.objects.create(
            code="R-API-SD",
            name="Ruta API Soft Delete",
        )
        self.url = f"/api/transport/routes/{self.route.id}/"

    def _auth(self):
        self.client.force_authenticate(user=self.admin)

    def test_delete_endpoint_returns_204(self):
        self._auth()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_endpoint_soft_deletes(self):
        self._auth()
        self.client.delete(self.url)
        self.route.refresh_from_db()
        self.assertFalse(self.route.is_active)

    def test_delete_endpoint_preserves_record(self):
        self._auth()
        self.client.delete(self.url)
        self.assertTrue(Route.all_objects.filter(id=self.route.id).exists())

    def test_inactive_not_listed(self):
        self._auth()
        route2 = Route.objects.create(
            code="R-API-ACTIVE",
            name="Ruta API Activa",
        )
        self.client.delete(self.url)

        response = self.client.get("/api/transport/routes/")
        results = response.json()["results"]
        ids = [r["id"] for r in results]
        self.assertNotIn(self.route.id, ids)
        self.assertIn(route2.id, ids)
        self.assertEqual(len(results), 1)

    def test_delete_endpoint_requires_auth(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BusStopAPISoftDeleteTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="sdbsadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))

    def setUp(self):
        self.stop = BusStop.objects.create(
            code="BS-API-SD",
            name="Parada API SD",
            latitude=-0.22,
            longitude=-78.52,
        )
        self.url = f"/api/transport/bus-stops/{self.stop.id}/"

    def test_delete_endpoint_soft_deletes_busstop(self):
        self.client.force_authenticate(user=self.admin)
        self.client.delete(self.url)
        self.stop.refresh_from_db()
        self.assertFalse(self.stop.is_active)
        self.assertTrue(BusStop.all_objects.filter(id=self.stop.id).exists())


class VehicleAPISoftDeleteTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="sdvehadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            plate="VH-API-SD",
            brand="SD Brand",
            model="SD Model",
            year=2024,
            capacity=60,
        )
        self.url = f"/api/transport/vehicles/{self.vehicle.id}/"

    def test_delete_endpoint_soft_deletes_vehicle(self):
        self.client.force_authenticate(user=self.admin)
        self.client.delete(self.url)
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.is_active)
        self.assertTrue(Vehicle.all_objects.filter(id=self.vehicle.id).exists())


class CatalogModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")

    def setUp(self):
        self.company = TransportCompany.objects.create(
            name="Empresa Test", tax_id="1234567890001",
        )
        self.district = District.objects.create(name="Distrito Test", code="D-TEST")
        self.sector = Sector.objects.create(
            district=self.district, name="Sector Test", code="S-TEST",
        )

    def test_company_str(self):
        self.assertEqual(str(self.company), f"{self.company.name} ({self.company.tax_id})")

    def test_district_str(self):
        self.assertEqual(str(self.district), f"{self.district.code} - {self.district.name}")

    def test_sector_str(self):
        expected = f"{self.sector.code} - {self.sector.name} ({self.district.code})"
        self.assertEqual(str(self.sector), expected)

    def test_soft_delete_transport_company(self):
        self.company.delete()
        self.company.refresh_from_db()
        self.assertFalse(self.company.is_active)
        self.assertNotIn(self.company, TransportCompany.objects.all())
        self.assertIn(self.company, TransportCompany.all_objects.all())

    def test_soft_delete_district(self):
        self.district.delete()
        self.district.refresh_from_db()
        self.assertFalse(self.district.is_active)

    def test_soft_delete_sector(self):
        self.sector.delete()
        self.sector.refresh_from_db()
        self.assertFalse(self.sector.is_active)

    def test_default_manager_filters_inactive_company(self):
        inactive = TransportCompany.objects.create(name="Inactiva", tax_id="8888888888888")
        inactive.delete()
        active = TransportCompany.objects.create(name="Activa", tax_id="9999999999999")
        self.assertEqual(TransportCompany.objects.count(), 2)
        self.assertIn(active, TransportCompany.objects.all())
        self.assertNotIn(inactive, TransportCompany.objects.all())

    def test_transport_company_ordering(self):
        b = TransportCompany.objects.create(name="B", tax_id="2222222222222")
        a = TransportCompany.objects.create(name="A", tax_id="1111111111111")
        qs = TransportCompany.objects.all()
        self.assertEqual(qs.first(), a)
        self.assertEqual(qs[1], b)
        self.assertEqual(qs.last(), self.company)


class CatalogAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        admin_group = Group.objects.get(name="Administrator")
        user_group = Group.objects.get(name="User")

        cls.admin = User.objects.create_user(
            username="catalogadmin",
            password="testpass123",
            email="admin@test.com",
        )
        cls.admin.groups.add(admin_group)

        cls.regular = User.objects.create_user(
            username="cataloguser",
            password="testpass123",
            email="user@test.com",
        )
        cls.regular.groups.add(user_group)

    def setUp(self):
        self.company = TransportCompany.objects.create(
            name="Empresa Original", tax_id="1799999999001",
        )
        self.district = District.objects.create(name="Centro", code="D-CEN")
        self.sector = Sector.objects.create(
            district=self.district, name="La Mariscal", code="S-LM",
        )

    # --- TransportCompany CRUD ---

    def test_list_companies_requires_auth(self):
        response = self.client.get("/api/transport/transport-companies/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_list_companies(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/transport-companies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_company(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/transport-companies/",
            {"name": "Nueva", "tax_id": "1111111111111"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_company(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/transport-companies/",
            {"name": "Admin Co", "tax_id": "1111111111111"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["name"], "Admin Co")

    def test_regular_user_cannot_update_company(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.patch(
            f"/api/transport/transport-companies/{self.company.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_company(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/transport/transport-companies/{self.company.id}/",
            {"name": "Actualizada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Actualizada")

    def test_regular_user_cannot_delete_company(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.delete(
            f"/api/transport/transport-companies/{self.company.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_company(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            f"/api/transport/transport-companies/{self.company.id}/",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_delete_soft_deletes_company(self):
        self.client.force_authenticate(user=self.admin)
        self.client.delete(f"/api/transport/transport-companies/{self.company.id}/")
        self.company.refresh_from_db()
        self.assertFalse(self.company.is_active)

    # --- District CRUD ---

    def test_regular_user_can_list_districts(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/districts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_district(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/districts/",
            {"name": "Norte", "code": "D-NOR"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_district(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/districts/",
            {"name": "Norte", "code": "D-NOR"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Sector CRUD ---

    def test_regular_user_can_filter_sectors_by_district(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            f"/api/transport/sectors/?district={self.district.id}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_admin_can_create_sector(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/sectors/",
            {"district": self.district.id, "name": "Nuevo", "code": "S-NVO"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["code"], "S-NVO")

    # --- VehicleType CRUD ---

    def test_admin_can_create_vehicle_type(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/vehicle-types/",
            {"name": "Bus", "code": "VT-BUS"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_vehicle_type(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/vehicle-types/",
            {"name": "Bus", "code": "VT-BUS"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- VehicleStatus CRUD ---

    def test_admin_can_create_vehicle_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/vehicle-statuses/",
            {"name": "Activo", "code": "VS-ACT"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_can_list_vehicle_statuses(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/vehicle-statuses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- Search and Filters ---

    # --- Route CRUD Permissions ---

    def test_regular_user_can_list_routes(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/routes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_route(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/routes/",
            {"code": "R-NO", "name": "No"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_route(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/routes/",
            {"code": "R-ADM", "name": "Admin Route"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- BusStop CRUD Permissions ---

    def test_regular_user_can_list_bus_stops(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/bus-stops/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_bus_stop(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/bus-stops/",
            {"code": "BS-NO", "name": "No", "latitude": 0, "longitude": 0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_bus_stop(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/bus-stops/",
            {"code": "BS-ADM", "name": "Admin Stop",
             "latitude": -0.22, "longitude": -78.52},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Vehicle CRUD Permissions ---

    def test_regular_user_cannot_create_vehicle(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/vehicles/",
            {"plate": "NO-001", "brand": "No", "model": "No",
             "year": 2020, "capacity": 10},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_vehicle(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/vehicles/",
            {"plate": "ADM-001", "brand": "Admin", "model": "Veh",
             "year": 2020, "capacity": 10},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Search and Filters ---

    def test_search_companies_by_name(self):
        TransportCompany.objects.create(name="Otra", tax_id="9999999999999")
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/transport-companies/?search=Original")
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["name"], "Empresa Original")

    def test_search_districts_by_code(self):
        District.objects.create(name="Sur", code="D-SUR")
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/districts/?search=CEN")
        self.assertEqual(len(response.json()["results"]), 1)
        self.assertEqual(response.json()["results"][0]["code"], "D-CEN")

    def test_filter_sectors_by_district(self):
        other = District.objects.create(name="Norte", code="D-NOR")
        Sector.objects.create(district=other, name="Cumbayá", code="S-CUM")
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(
            f"/api/transport/sectors/?district={self.district.id}",
        )
        self.assertEqual(len(response.json()["results"]), 1)

    # --- Pagination ---

    def test_pagination_default_page_size(self):
        self.client.force_authenticate(user=self.admin)
        for i in range(25):
            TransportCompany.objects.create(
                name=f"Co {i}", tax_id=f"{i:013d}",
            )
        response = self.client.get("/api/transport/transport-companies/")
        self.assertEqual(len(response.json()["results"]), 20)
        self.assertIsNotNone(response.json()["next"])


# ----------------------------------------------------------------
# RouteBusStop Tests
# ----------------------------------------------------------------

class RouteBusStopModelTest(TestCase):
    def setUp(self):
        self.route = Route.objects.create(code="R-RBS", name="Ruta RBS")
        self.stop = BusStop.objects.create(
            code="BS-RBS", name="Parada RBS",
            latitude=-0.22, longitude=-78.52,
        )
        self.rbs = RouteBusStop.objects.create(
            route=self.route, bus_stop=self.stop,
            stop_order=1, estimated_minutes_from_start=5,
        )

    def test_str(self):
        expected = f"{self.route.code} - {self.stop.code} (orden 1)"
        self.assertEqual(str(self.rbs), expected)

    def test_soft_delete(self):
        self.rbs.delete()
        self.rbs.refresh_from_db()
        self.assertFalse(self.rbs.is_active)

    def test_unique_stop_order_per_route(self):
        other_stop = BusStop.objects.create(
            code="BS-RBS2", name="Otra",
            latitude=-0.23, longitude=-78.53,
        )
        with self.assertRaises(Exception):
            RouteBusStop.objects.create(
                route=self.route, bus_stop=other_stop,
                stop_order=1,
            )

    def test_unique_bus_stop_per_route(self):
        with self.assertRaises(Exception):
            RouteBusStop.objects.create(
                route=self.route, bus_stop=self.stop,
                stop_order=2,
            )

    def test_ordering(self):
        stop2 = BusStop.objects.create(
            code="BS-RBS3", name="Tercera",
            latitude=-0.24, longitude=-78.54,
        )
        rbs2 = RouteBusStop.objects.create(
            route=self.route, bus_stop=stop2,
            stop_order=2,
        )
        qs = RouteBusStop.objects.all()
        self.assertEqual(qs.first(), self.rbs)
        self.assertEqual(qs.last(), rbs2)


class RouteBusStopAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_groups")
        cls.admin = User.objects.create_user(
            username="rbsadmin", password="testpass123",
        )
        cls.admin.groups.add(Group.objects.get(name="Administrator"))
        cls.regular = User.objects.create_user(
            username="rbsuser", password="testpass123",
        )
        cls.regular.groups.add(Group.objects.get(name="User"))

    def setUp(self):
        self.route = Route.objects.create(code="R-RBS-API", name="Ruta API")
        self.stop = BusStop.objects.create(
            code="BS-RBS-API", name="Parada API",
            latitude=-0.22, longitude=-78.52,
        )

    def test_admin_can_create(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": self.stop.id,
             "stop_order": 1, "estimated_minutes_from_start": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_can_list(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get("/api/transport/route-bus-stops/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": self.stop.id,
             "stop_order": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_stop_order_validation(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": self.stop.id,
             "stop_order": 1},
            format="json",
        )
        other = BusStop.objects.create(
            code="BS-OTHER", name="Otra",
            latitude=-0.23, longitude=-78.53,
        )
        response = self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": other.id,
             "stop_order": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_bus_stop_validation(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": self.stop.id,
             "stop_order": 1},
            format="json",
        )
        response = self.client.post(
            "/api/transport/route-bus-stops/",
            {"route": self.route.id, "bus_stop": self.stop.id,
             "stop_order": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_route(self):
        self.client.force_authenticate(user=self.admin)
        RouteBusStop.objects.create(
            route=self.route, bus_stop=self.stop, stop_order=1,
        )
        response = self.client.get(
            f"/api/transport/route-bus-stops/?route={self.route.id}"
        )
        self.assertGreaterEqual(len(response.json()["results"]), 1)

    def test_admin_can_delete_soft(self):
        rbs = RouteBusStop.objects.create(
            route=self.route, bus_stop=self.stop, stop_order=1,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/transport/route-bus-stops/{rbs.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        rbs.refresh_from_db()
        self.assertFalse(rbs.is_active)
