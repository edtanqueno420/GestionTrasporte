from datetime import UTC, date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.incidents.models import Incident, IncidentType
from apps.operations.models import (
    Driver,
    DriverAssignment,
    GPSPosition,
    RouteCoordinate,
    Schedule,
    Trip,
)
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


class Command(BaseCommand):
    help = "Seed database with demo data for QuitoMove"

    QUITO_LAT = -0.22985
    QUITO_LNG = -78.52495

    def handle(self, *args, **options):
        self._create_catalogs()
        route_stops, vehicle = self._create_route_and_stops()
        driver_user, normal_user, driver = self._create_users_and_driver()
        self._create_driver_assignment(driver, vehicle)
        schedule = self._create_schedule(route_stops["route"])
        trip = self._create_trip(route_stops["route"], vehicle, driver, schedule)
        self._create_initial_gps(trip, route_stops["stops"])
        self._create_incident(trip)
        self._create_route_coordinates(trip.route, route_stops["stops"])
        self.stdout.write(self.style.SUCCESS("\n✅ DEMO DATA READY"))
        self._print_summary(
            route_stops["route"], vehicle, driver_user, normal_user, trip, driver,
        )

    @transaction.atomic
    def _create_catalogs(self):
        self.company, _ = TransportCompany.objects.get_or_create(
            tax_id="1790012345001",
            defaults=dict(
                name="Ecovía Transporte S.A.",
                phone="+593 2 2555 555",
                email="info@ecovia.quito.gob.ec",
                address="Av. Río Coca y Naciones Unidas, Quito",
            ),
        )
        self.district, _ = District.objects.get_or_create(
            code="DIS-QTO",
            defaults=dict(name="Distrito Metropolitano de Quito"),
        )
        self.sector, _ = Sector.objects.get_or_create(
            code="SEC-NORTE",
            district=self.district,
            defaults=dict(name="Sector Norte"),
        )
        self.vtype, _ = VehicleType.objects.get_or_create(
            code="VT-BUS",
            defaults=dict(name="Bus Articulado"),
        )
        self.vstatus, _ = VehicleStatus.objects.get_or_create(
            code="VS-ACTIVE",
            defaults=dict(name="Activo"),
        )
        for code, name in [
            ("IT-ACC", "Accidente"),
            ("IT-MEC", "Falla Mecánica"),
            ("IT-RET", "Retraso"),
        ]:
            IncidentType.objects.get_or_create(code=code, defaults=dict(name=name))

    def _create_route_and_stops(self):
        route, _ = Route.objects.get_or_create(
            code="RT-ECO",
            defaults=dict(
                name="Ecovía Norte-Sur",
                description="Ruta troncal Ecovía desde Terminal Río Coca hasta Quitumbe",
                transport_company=self.company,
            ),
        )
        stops_data = [
            ("BS-RIO", "Terminal Río Coca", -0.1694, -78.4779, 0),
            ("BS-CAR", "La Carolina", -0.1845, -78.4828, 8),
            ("BS-EJI", "El Ejido", -0.2005, -78.4900, 15),
            ("BS-MAR", "Marín Central", -0.2150, -78.4990, 22),
            ("BS-CUM", "Cumandá", -0.2250, -78.5070, 28),
            ("BS-REC", "Recreo", -0.2400, -78.5120, 35),
            ("BS-QUI", "Quitumbe", -0.2850, -78.5300, 50),
        ]
        stops = []
        for code, name, lat, lng, mins in stops_data:
            stop, _ = BusStop.objects.get_or_create(
                code=code,
                defaults=dict(name=name, latitude=lat, longitude=lng, sector=self.sector),
            )
            stops.append(stop)
        for i, stop in enumerate(stops):
            RouteBusStop.objects.get_or_create(
                route=route, bus_stop=stop,
                defaults=dict(
                    stop_order=i + 1,
                    estimated_minutes_from_start=stops_data[i][4] or None,
                ),
            )
        vehicle, _ = Vehicle.objects.get_or_create(
            plate="ECO-001",
            defaults=dict(
                brand="Volvo", model="B340M", year=2021, capacity=160,
                transport_company=self.company,
                vehicle_type=self.vtype, vehicle_status=self.vstatus,
            ),
        )
        return {"route": route, "stops": stops}, vehicle

    def _create_route_coordinates(self, route, stops):
        if RouteCoordinate.objects.filter(route=route).exists():
            return
        interp_points = []
        for i in range(len(stops) - 1):
            lat1, lng1 = float(stops[i].latitude), float(stops[i].longitude)
            lat2, lng2 = float(stops[i + 1].latitude), float(stops[i + 1].longitude)
            for j in range(4):
                t = j / 4
                interp_points.append((
                    lat1 + (lat2 - lat1) * t,
                    lng1 + (lng2 - lng1) * t,
                ))
        interp_points.append((float(stops[-1].latitude), float(stops[-1].longitude)))
        for i, (lat, lng) in enumerate(interp_points):
            RouteCoordinate.objects.create(
                route=route, latitude=lat, longitude=lng, order=i + 1,
            )
        self.stdout.write(f"  RouteCoordinates: {len(interp_points)} puntos")

    def _create_users_and_driver(self):
        driver_user, _ = User.objects.get_or_create(
            username="conductor1",
            defaults=dict(
                email="conductor@ecovia.ec",
            ),
        )
        if not driver_user.password or driver_user.password.startswith("!"):
            driver_user.set_password("demo123")
            driver_user.save()
        normal_user, _ = User.objects.get_or_create(
            username="usuario1",
            defaults=dict(
                email="usuario@demo.ec",
            ),
        )
        if not normal_user.password or normal_user.password.startswith("!"):
            normal_user.set_password("demo123")
            normal_user.save()
        driver, _ = Driver.objects.get_or_create(
            user=driver_user,
            defaults=dict(
                license_number="LIC-DEMO-001",
                license_type=Driver.LicenseType.C,
                hire_date=date(2023, 1, 15),
                experience_years=5,
                is_available=False,
            ),
        )
        return driver_user, normal_user, driver

    def _create_driver_assignment(self, driver, vehicle):
        DriverAssignment.objects.get_or_create(
            driver=driver, vehicle=vehicle,
            defaults=dict(
                assignment_date=date.today(),
                is_active_assignment=True,
            ),
        )

    def _create_schedule(self, route):
        schedule, _ = Schedule.objects.get_or_create(
            route=route, departure_time=time(6, 0),
            defaults=dict(
                arrival_time=time(7, 0),
                frequency_minutes=15,
                operating_days="1234567",
            ),
        )
        return schedule

    def _create_trip(self, route, vehicle, driver, schedule):
        now_utc = datetime.now(UTC)
        trip = Trip.objects.filter(
            route=route, vehicle=vehicle, driver=driver,
            trip_date=date.today(), is_active=True,
        ).last()
        if trip:
            trip.departure_datetime = now_utc - timedelta(minutes=30)
            trip.status = Trip.Status.IN_PROGRESS
            trip.save(update_fields=["departure_datetime", "status"])
        else:
            trip = Trip.objects.create(
                route=route, vehicle=vehicle, driver=driver,
                trip_date=date.today(),
                departure_datetime=now_utc - timedelta(minutes=30),
                schedule=schedule,
                status=Trip.Status.IN_PROGRESS,
                passenger_count=85,
                observations="Viaje demo Ecovía Norte-Sur",
            )
        return trip

    def _create_initial_gps(self, trip, stops):
        if GPSPosition.objects.filter(trip=trip).exists():
            return
        lat1, lng1 = float(stops[0].latitude), float(stops[0].longitude)
        lat2, lng2 = float(stops[2].latitude), float(stops[2].longitude)
        now_utc = datetime.now(UTC)
        GPSPosition.objects.create(
            trip=trip,
            latitude=lat1, longitude=lng1,
            speed=0, heading=180,
            recorded_at=now_utc - timedelta(minutes=5),
        )
        GPSPosition.objects.create(
            trip=trip,
            latitude=(lat1 + lat2) / 2, longitude=(lng1 + lng2) / 2,
            speed=25.5, heading=185,
            recorded_at=now_utc - timedelta(minutes=3),
        )
        GPSPosition.objects.create(
            trip=trip,
            latitude=lat2, longitude=lng2,
            speed=35.0, heading=190,
            recorded_at=now_utc - timedelta(minutes=1),
        )
        self.stdout.write("  GPSPositions: 3 iniciales")

    def _create_incident(self, trip):
        if Incident.objects.filter(trip=trip).exists():
            return
        accident_type = IncidentType.objects.get(code="IT-ACC")
        lat = float(trip.route.route_stops.first().bus_stop.latitude)
        lng = float(trip.route.route_stops.first().bus_stop.longitude)
        Incident.objects.create(
            trip=trip,
            incident_type=accident_type,
            vehicle=trip.vehicle,
            latitude=lat + 0.002,
            longitude=lng + 0.002,
            description="Freno de emergencia por obstáculo en la vía",
            severity=Incident.Severity.LOW,
            status=Incident.Status.OPEN,
        )
        self.stdout.write("  Incident: 1 abierto (ejemplo)")

    def _print_summary(self, route, vehicle, driver_user, normal_user, trip, driver):
        self.stdout.write(f"\n📋 Route:          {route.code} - {route.name} (PK={route.id})")
        self.stdout.write(f"🚍 Vehicle:        {vehicle.plate} (PK={vehicle.id})")
        self.stdout.write(f"👤 Conductor:      {driver_user.username} / demo123")
        self.stdout.write(f"👤 Usuario:        {normal_user.username} / demo123")
        self.stdout.write(f"🛤️  Trip (en curso): {trip.id} (PK={trip.id})")
        self.stdout.write(f"\n📌 Para Postman: route_id={route.id} vehicle_id={vehicle.id} trip_id={trip.id} driver_id={driver.pk}")
        self.stdout.write(f"\nEjecute:  python manage.py simulate_gps --trip_id={trip.id}")
