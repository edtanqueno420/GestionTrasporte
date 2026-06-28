from datetime import UTC, datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from time import sleep

from django.core.management.base import BaseCommand, CommandError

from apps.operations.models import GPSPosition, RouteCoordinate, Trip


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


class Command(BaseCommand):
    help = "Simulate GPS movement along a trip's route coordinates"

    def add_arguments(self, parser):
        parser.add_argument("--trip_id", type=int, required=True, help="Trip ID to simulate")

    def handle(self, *args, **options):
        trip_id = options["trip_id"]
        try:
            trip = Trip.objects.select_related("route").get(pk=trip_id)
        except Trip.DoesNotExist:
            raise CommandError(f"Trip {trip_id} no encontrado")

        route = trip.route
        coords = list(RouteCoordinate.objects.filter(
            route=route, is_active=True,
        ).order_by("order"))

        if len(coords) < 2:
            self.stdout.write(self.style.WARNING(
                "Menos de 2 RouteCoordinates. Caigo a BusStops."
            ))
            stops = list(route.route_stops.filter(
                is_active=True,
            ).select_related("bus_stop").order_by("stop_order"))
            if len(stops) < 2:
                raise CommandError("No hay suficientes puntos para simular")
            points = [(float(s.bus_stop.latitude), float(s.bus_stop.longitude)) for s in stops]
        else:
            points = [(float(c.latitude), float(c.longitude)) for c in coords]

        self.stdout.write(self.style.SUCCESS(
            f"Simulando GPS para Trip {trip_id} — {len(points)} puntos"
        ))
        self.stdout.write("Presione CTRL+C para detener.\n")

        try:
            self._run_simulation(trip, points)
        except KeyboardInterrupt:
            self.stdout.write("\nSimulación detenida.")

    def _run_simulation(self, trip, points):
        idx = 0
        step = 0
        total_distance = sum(
            _haversine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
            for i in range(len(points) - 1)
        )
        self.stdout.write(f"  Distancia total: {total_distance / 1000:.2f} km")

        while True:
            speed, head, idx = self._next_movement(points, idx, step)
            lat, lng = points[idx]
            now_utc = datetime.now(UTC)
            GPSPosition.objects.create(
                trip=trip,
                latitude=lat, longitude=lng,
                speed=round(speed, 2),
                heading=round(head, 2),
                recorded_at=now_utc,
            )
            progress = (idx / (len(points) - 1)) * 100
            self.stdout.write(
                f"  [{idx+1:03d}/{len(points):03d}] "
                f"({lat:.6f}, {lng:.6f}) "
                f"{speed:.1f} km/h  {progress:.0f}%"
            )
            step += 1
            delay = 3 + (step % 2) * 2
            sleep(delay)

    def _next_movement(self, points, idx, step):
        n = len(points)
        progress = idx / (n - 1) if n > 1 else 0

        speed = 0
        if progress < 0.15:
            speed = 10 + 30 * (progress / 0.15)
        elif progress > 0.85:
            speed = 40 - 40 * ((progress - 0.85) / 0.15)
        else:
            speed = 35 + 5 * (step % 3)

        if idx < n - 1:
            lat1, lng1 = points[idx]
            lat2, lng2 = points[idx + 1]
            head = atan2(
                radians(lng2 - lng1),
                radians(lat2 - lat1),
            ) * 180 / 3.14159
            head = head % 360
            if (step % 3) == 0:
                idx += 1
        else:
            head = 0
            idx = 0

        return speed, head, idx
