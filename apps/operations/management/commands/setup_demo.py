from datetime import UTC, datetime

from django.core.management.base import BaseCommand

from apps.operations.models import GPSPosition, RouteCoordinate, Trip
from apps.incidents.models import Incident, IncidentType


def _interpolate(p1, p2, t):
    return p1 + (p2 - p1) * t


def _heading(lat1, lng1, lat2, lng2):
    from math import atan2, radians, degrees
    dlng = radians(lng2 - lng1)
    dlat = radians(lat2 - lat1)
    head = atan2(dlng, dlat) * 180 / 3.14159
    return head % 360


class Command(BaseCommand):
    help = "Setup demo data: activate trips, create GPS positions, create incidents near UTE"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SETUP DEMO ===\n"))

        self._activate_trips()
        self._create_gps_positions()
        self._create_incidents()

        self.stdout.write(self.style.SUCCESS("\n=== DEMO LISTO ==="))
        self.stdout.write("  GET /api/operations/gps-positions/active/ → buses en mapa")
        self.stdout.write("  GET /api/incidents/incidents/nearby/?lat=-0.1807&lng=-78.4678&radius_km=10 → incidentes cercanos")

    def _activate_trips(self):
        self.stdout.write("1. Activando trips...")
        trips = Trip.objects.filter(is_active=True)
        now = datetime.now(UTC)

        for trip in trips:
            trip.status = Trip.Status.IN_PROGRESS
            trip.departure_datetime = now
            trip.save(update_fields=["status", "departure_datetime"])
            self.stdout.write(f"   Trip {trip.id}: {trip.route.code} - {trip.vehicle.plate} → in_progress")

        self.stdout.write(self.style.SUCCESS(f"   {trips.count()} trips activados\n"))

    def _create_gps_positions(self):
        self.stdout.write("2. Creando posiciones GPS iniciales...")

        trips = Trip.objects.filter(
            status=Trip.Status.IN_PROGRESS,
            is_active=True,
        ).select_related("route")

        now = datetime.now(UTC)

        positions_config = {
            0: 0.2,
            1: 0.5,
            2: 0.75,
            3: 0.4,
        }

        for idx, trip in enumerate(trips):
            coords = list(
                RouteCoordinate.objects.filter(
                    route=trip.route, is_active=True
                ).order_by("order")
            )

            if len(coords) < 2:
                self.stdout.write(self.style.WARNING(
                    f"   Trip {trip.id}: menos de 2 coordenadas, saltando"
                ))
                continue

            progress = positions_config.get(idx, 0.3)
            n = len(coords) - 1
            seg = min(int(progress * n), n - 1)
            local_t = (progress * n) - seg

            lat = _interpolate(
                float(coords[seg].latitude),
                float(coords[seg + 1].latitude),
                local_t,
            )
            lng = _interpolate(
                float(coords[seg].longitude),
                float(coords[seg + 1].longitude),
                local_t,
            )

            heading = _heading(
                float(coords[seg].latitude),
                float(coords[seg].longitude),
                float(coords[seg + 1].latitude),
                float(coords[seg + 1].longitude),
            )

            speed = 25 + 10 * (idx % 3)

            GPSPosition.objects.create(
                trip=trip,
                latitude=round(lat, 6),
                longitude=round(lng, 6),
                speed=round(speed, 2),
                heading=round(heading, 2),
                recorded_at=now,
            )
            self.stdout.write(
                f"   Trip {trip.id} ({trip.route.code}): "
                f"({lat:.6f}, {lng:.6f}) "
                f"{speed:.0f} km/h heading {heading:.0f}°"
            )

        self.stdout.write(self.style.SUCCESS(f"   Posiciones creadas para {trips.count()} trips\n"))

    def _create_incidents(self):
        self.stdout.write("3. Verificando incidentes cercanos a UTE Matriz...")

        UTE_LAT = -0.1807
        UTE_LNG = -78.4678

        existing = Incident.objects.filter(
            is_active=True,
            latitude__range=(-0.19, -0.17),
            longitude__range=(-78.48, -78.46),
        ).count()

        if existing > 0:
            self.stdout.write(self.style.SUCCESS(f"   Ya existen {existing} incidentes cerca de UTE\n"))
            return

        trip = Trip.objects.filter(
            status=Trip.Status.IN_PROGRESS,
            is_active=True,
        ).first()

        if not trip:
            self.stdout.write(self.style.WARNING("   No hay trips activos para crear incidentes"))
            return

        incident_type = IncidentType.objects.filter(is_active=True).first()
        if not incident_type:
            self.stdout.write(self.style.WARNING("   No hay tipos de incidente"))
            return

        incidents_data = [
            {
                "latitude": -0.1812,
                "longitude": -78.4690,
                "severity": "high",
                "description": "Accidente en la intersección cerca de UTE Matriz",
            },
            {
                "latitude": -0.1795,
                "longitude": -78.4665,
                "severity": "medium",
                "description": "Retraso por tráfico pesado enSector Rumipamba",
            },
            {
                "latitude": -0.1820,
                "longitude": -78.4710,
                "severity": "low",
                "description": "Falla mecánica en parada cercana",
            },
        ]

        for data in incidents_data:
            Incident.objects.create(
                trip=trip,
                incident_type=incident_type,
                vehicle=trip.vehicle,
                driver=trip.driver,
                latitude=data["latitude"],
                longitude=data["longitude"],
                description=data["description"],
                severity=data["severity"],
                status=Incident.Status.OPEN,
            )
            self.stdout.write(
                f"   Incidente: {data['severity']} @ "
                f"({data['latitude']}, {data['longitude']})"
            )

        self.stdout.write(self.style.SUCCESS(f"   {len(incidents_data)} incidentes creados\n"))
