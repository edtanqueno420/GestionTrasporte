from datetime import UTC, date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from django.contrib.auth.models import Group

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


def _interpolate_stops(stops, points_between=4):
    points = []
    for i in range(len(stops) - 1):
        lat1, lng1 = float(stops[i][2]), float(stops[i][3])
        lat2, lng2 = float(stops[i + 1][2]), float(stops[i + 1][3])
        for j in range(points_between):
            t = j / points_between
            points.append((lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t))
    points.append((float(stops[-1][2]), float(stops[-1][3])))
    return points


class Command(BaseCommand):
    help = "Seed database with demo data for QuitoMove"

    ROUTE_DEFS = [
        {
            "route": {
                "code": "RT-ECO", "name": "Ecovía Norte-Sur",
                "desc": "Ruta troncal Ecovía desde Terminal Río Coca hasta Quitumbe",
                "company_key": "ecovia",
            },
            "sector": ("SEC-NORTE", "Sector Norte"),
            "stops": [
                ("BS-RIO", "Terminal Río Coca", -0.1694, -78.4779, 0),
                ("BS-CAR", "La Carolina", -0.1845, -78.4828, 8),
                ("BS-EJI", "El Ejido", -0.2005, -78.4900, 15),
                ("BS-MAR", "Marín Central", -0.2150, -78.4990, 22),
                ("BS-CUM", "Cumandá", -0.2250, -78.5070, 28),
                ("BS-REC", "Recreo", -0.2400, -78.5120, 35),
                ("BS-QUI", "Quitumbe", -0.2850, -78.5300, 50),
            ],
            "vehicle": {
                "plate": "ECO-001", "brand": "Volvo", "model": "B340M",
                "year": 2021, "capacity": 160, "company_key": "ecovia",
            },
            "driver": {
                "username": "conductor1", "email": "conductor@ecovia.ec",
                "licence": "LIC-DEMO-001",
            },
            "schedule": {"departure": time(6, 0), "arrival": time(7, 0), "freq": 15},
            "trip": {
                "obs": "Viaje demo Ecovía Norte-Sur",
                "passengers": 85,
            },
            "incident": {
                "desc": "Freno de emergencia por obstáculo en la vía",
                "severity": Incident.Severity.LOW,
            },
        },
        {
            "route": {
                "code": "RT-TRO", "name": "Trolebús Carcelén-Quitumbe",
                "desc": "Corredor central trolebús desde Terminal Carcelén hasta Terminal Quitumbe vía Av. 10 de Agosto",
                "company_key": "trolebus",
            },
            "sector": ("SEC-CENTRO", "Sector Centro"),
            "stops": [
                ("BS-CRN", "Terminal Carcelén", -0.1250, -78.4950, 0),
                ("BS-COT", "Cotocollao", -0.1400, -78.4930, 5),
                ("BS-CEN", "Estación Central", -0.1950, -78.4980, 18),
                ("BS-PLA", "Plaza Grande", -0.2200, -78.5120, 25),
                ("BS-SRO", "San Roque", -0.2350, -78.5180, 30),
                ("BS-CHI", "Chimbacalle", -0.2500, -78.5250, 38),
                ("BS-QUI", "Quitumbe", -0.2850, -78.5300, 50),
            ],
            "vehicle": {
                "plate": "TRO-001", "brand": "Mercedes-Benz", "model": "O500U",
                "year": 2022, "capacity": 180, "company_key": "trolebus",
            },
            "driver": {
                "username": "conductor2", "email": "conductor2@trolebus.ec",
                "licence": "LIC-DEMO-002",
            },
            "schedule": {"departure": time(5, 30), "arrival": time(6, 30), "freq": 10},
            "trip": {
                "obs": "Viaje demo Trolebús",
                "passengers": 120,
            },
        },
        {
            "route": {
                "code": "RT-ME1", "name": "Metrovía Río Coca – Recreo",
                "desc": "Corredor Metrovía desde Terminal Río Coca hasta El Recreo por Av. 6 de Diciembre y Av. Pichincha",
                "company_key": "metrovia",
            },
            "sector": ("SEC-CENTRO", "Sector Centro"),
            "stops": [
                ("BS-RIO", "Terminal Río Coca", -0.1694, -78.4779, 0),
                ("BS-IPC", "Iñaquito", -0.1820, -78.4800, 6),
                ("BS-BEN", "Benalcázar", -0.2000, -78.4850, 14),
                ("BS-BEL", "Bellavista", -0.2080, -78.4900, 20),
                ("BS-MAR", "Marín Central", -0.2150, -78.4990, 28),
                ("BS-SRO", "San Roque", -0.2350, -78.5180, 36),
                ("BS-REC", "El Recreo", -0.2400, -78.5120, 40),
            ],
            "vehicle": {
                "plate": "MET-001", "brand": "Scania", "model": "K320", "year": 2023,
                "capacity": 140, "company_key": "metrovia",
            },
            "driver": {
                "username": "conductor3", "email": "conductor3@metrovia.ec",
                "licence": "LIC-DEMO-003",
            },
            "schedule": {"departure": time(6, 15), "arrival": time(7, 5), "freq": 12},
            "trip": {
                "obs": "Viaje demo Metrovía",
                "passengers": 95,
            },
        },
        {
            "route": {
                "code": "RT-SUR", "name": "Corredor Sur Los Shyris – Quitumbe",
                "desc": "Corredor complementario desde Av. Los Shyris hasta Quitumbe por Av. América y Av. Maldonado",
                "company_key": "trolebus",
            },
            "sector": ("SEC-SUR", "Sector Sur"),
            "stops": [
                ("BS-SHY", "Los Shyris", -0.1720, -78.4760, 0),
                ("BS-CRI", "Cristianía", -0.1920, -78.4800, 10),
                ("BS-HER", "Hernando de la Cruz", -0.2100, -78.4920, 20),
                ("BS-SOL", "Solanda", -0.2400, -78.5050, 30),
                ("BS-CHA", "Chilibulo", -0.2600, -78.5200, 38),
                ("BS-QUI", "Quitumbe", -0.2850, -78.5300, 48),
            ],
            "vehicle": {
                "plate": "SUR-001", "brand": "Hino", "model": "AK8J",
                "year": 2023, "capacity": 90, "company_key": "trolebus",
            },
            "driver": {
                "username": "conductor4", "email": "conductor4@trolebus.ec",
                "licence": "LIC-DEMO-004",
            },
            "schedule": {"departure": time(6, 30), "arrival": time(7, 20), "freq": 20},
            "trip": {
                "obs": "Viaje demo Corredor Sur",
                "passengers": 60,
            },
        },
    ]

    def handle(self, *args, **options):
        self._create_catalogs()
        self._create_companies()
        self._create_users()

        trips = []
        for rdef in self.ROUTE_DEFS:
            trip = self._build_route(rdef)
            trips.append(trip)
            self.stdout.write(f"  OK {rdef['route']['code']} - {rdef['route']['name']}")

        self.stdout.write(self.style.SUCCESS("\nEVERYTHING READY"))
        self._print_summary(trips)

    @transaction.atomic
    def _create_catalogs(self):
        self.district, _ = District.objects.get_or_create(
            code="DIS-QTO",
            defaults=dict(name="Distrito Metropolitano de Quito"),
        )
        for code, name in [("SEC-NORTE", "Sector Norte"), ("SEC-CENTRO", "Sector Centro"),
                           ("SEC-SUR", "Sector Sur"), ("SEC-VALLES", "Sector Valles")]:
            Sector.objects.get_or_create(code=code, district=self.district, defaults=dict(name=name))
        self.vtype, _ = VehicleType.objects.get_or_create(
            code="VT-BUS", defaults=dict(name="Bus Articulado"),
        )
        self.vstatus, _ = VehicleStatus.objects.get_or_create(
            code="VS-ACTIVE", defaults=dict(name="Activo"),
        )
        for code, name in [("IT-ACC", "Accidente"), ("IT-MEC", "Falla Mecánica"), ("IT-RET", "Retraso")]:
            IncidentType.objects.get_or_create(code=code, defaults=dict(name=name))

    def _create_companies(self):
        self.companies = {}
        companies_data = [
            ("ecovia", "1790012345001", "Ecovía Transporte S.A.",
             "+593 2 2555 555", "info@ecovia.quito.gob.ec",
             "Av. Río Coca y Naciones Unidas, Quito"),
            ("trolebus", "1790012345002", "Empresa Trolebús Quito",
             "+593 2 2998 100", "info@trolebus.gob.ec",
             "Av. 10 de Agosto y Núñez de Vela, Quito"),
            ("metrovia", "1790012345003", "Metrovía Quito S.A.",
             "+593 2 2998 200", "info@metrovia.gob.ec",
             "Av. 6 de Diciembre y Patria, Quito"),
        ]
        for key, tax_id, name, phone, email, addr in companies_data:
            company, _ = TransportCompany.objects.get_or_create(
                tax_id=tax_id, defaults=dict(name=name, phone=phone, email=email, address=addr),
            )
            self.companies[key] = company

    def _create_users(self):
        users_data = [
            ("admin", "admin@movicore.ec", True, "Administrator"),
            ("conductor1", "conductor@ecovia.ec", False, None),
            ("conductor2", "conductor2@trolebus.ec", False, None),
            ("conductor3", "conductor3@metrovia.ec", False, None),
            ("conductor4", "conductor4@trolebus.ec", False, None),
            ("usuario1", "usuario@demo.ec", False, None),
        ]
        for username, email, is_staff, group_name in users_data:
            u, _ = User.objects.get_or_create(username=username, defaults=dict(email=email, is_staff=is_staff))
            if not u.password or u.password.startswith("!"):
                u.set_password("demo123")
                u.save()
            if group_name:
                group = Group.objects.get_or_create(name=group_name)[0]
                u.groups.add(group)

    def _get_sector(self, code):
        return Sector.objects.get(code=code)

    def _build_route(self, rdef):
        route_code = rdef["route"]["code"]

        route, _ = Route.objects.get_or_create(
            code=route_code,
            defaults=dict(
                name=rdef["route"]["name"],
                description=rdef["route"]["desc"],
                transport_company=self.companies[rdef["route"]["company_key"]],
            ),
        )

        sector_code = rdef["sector"][0]
        sector = self._get_sector(sector_code)

        stops_data = rdef["stops"]
        stops = []
        for code, name, lat, lng, mins in stops_data:
            stop, _ = BusStop.objects.get_or_create(
                code=code,
                defaults=dict(name=name, latitude=lat, longitude=lng, sector=sector),
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

        self._create_route_coordinates(route, stops_data)

        vdef = rdef["vehicle"]
        vehicle, _ = Vehicle.objects.get_or_create(
            plate=vdef["plate"],
            defaults=dict(
                brand=vdef["brand"], model=vdef["model"], year=vdef["year"],
                capacity=vdef["capacity"],
                transport_company=self.companies[vdef["company_key"]],
                vehicle_type=self.vtype, vehicle_status=self.vstatus,
            ),
        )

        ddef = rdef["driver"]
        driver_user = User.objects.get(username=ddef["username"])
        driver, _ = Driver.objects.get_or_create(
            user=driver_user,
            defaults=dict(
                license_number=ddef["licence"],
                license_type=Driver.LicenseType.C,
                hire_date=date(2023, 1, 15),
                experience_years=5,
                is_available=False,
            ),
        )

        DriverAssignment.objects.get_or_create(
            driver=driver, vehicle=vehicle,
            defaults=dict(assignment_date=date.today(), is_active_assignment=True),
        )

        sdef = rdef["schedule"]
        schedule, _ = Schedule.objects.get_or_create(
            route=route, departure_time=sdef["departure"],
            defaults=dict(
                arrival_time=sdef["arrival"],
                frequency_minutes=sdef["freq"],
                operating_days="1234567",
            ),
        )

        now_utc = datetime.now(UTC)
        tdef = rdef["trip"]
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
                schedule=schedule, status=Trip.Status.IN_PROGRESS,
                passenger_count=tdef.get("passengers", 80),
                observations=tdef.get("obs", ""),
            )

        self._create_initial_gps(trip, stops_data)

        incident_def = rdef.get("incident")
        if incident_def and not Incident.objects.filter(trip=trip).exists():
            atype = IncidentType.objects.get(code="IT-ACC")
            lat, lng = stops_data[0][2], stops_data[0][3]
            Incident.objects.create(
                trip=trip, incident_type=atype, vehicle=vehicle,
                latitude=lat + 0.002, longitude=lng + 0.002,
                description=incident_def["desc"],
                severity=incident_def.get("severity", Incident.Severity.LOW),
                status=Incident.Status.OPEN,
            )

        return trip

    def _create_route_coordinates(self, route, stops_data):
        if RouteCoordinate.objects.filter(route=route).exists():
            return
        points = _interpolate_stops(stops_data)
        for i, (lat, lng) in enumerate(points):
            RouteCoordinate.objects.create(
                route=route, latitude=lat, longitude=lng, order=i + 1,
            )

    def _create_initial_gps(self, trip, stops_data):
        if GPSPosition.objects.filter(trip=trip).exists():
            return
        lat1, lng1 = stops_data[0][2], stops_data[0][3]
        lat2, lng2 = stops_data[2][2], stops_data[2][3]
        now_utc = datetime.now(UTC)
        GPSPosition.objects.create(
            trip=trip, latitude=lat1, longitude=lng1,
            speed=0, heading=180,
            recorded_at=now_utc - timedelta(minutes=5),
        )
        GPSPosition.objects.create(
            trip=trip, latitude=(lat1 + lat2) / 2, longitude=(lng1 + lng2) / 2,
            speed=25.5, heading=185,
            recorded_at=now_utc - timedelta(minutes=3),
        )
        GPSPosition.objects.create(
            trip=trip, latitude=lat2, longitude=lng2,
            speed=35.0, heading=190,
            recorded_at=now_utc - timedelta(minutes=1),
        )

    def _print_summary(self, trips):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"{'Ruta':<12} {'Nombre':<28} {'Viaje ID':<10} {'Simular GPS'}")
        self.stdout.write("-" * 60)
        for t in trips:
            self.stdout.write(f"{t.route.code:<12} {t.route.name:<28} {t.id:<10} "
                              f"python manage.py simulate_gps --trip_id={t.id}")
        self.stdout.write("=" * 60)
        self.stdout.write("\nUsuarios disponibles: admin / demo123 (staff)")
        self.stdout.write("                     conductor1-4 / demo123")
        self.stdout.write("                     usuario1 / demo123")
