from datetime import UTC, datetime
from math import atan2, radians, sin, cos, sqrt
from time import sleep

from django.core.management.base import BaseCommand

from apps.operations.models import GPSPosition, RouteCoordinate, Trip


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _interpolate(p1, p2, t):
    return p1 + (p2 - p1) * t


def _heading(lat1, lng1, lat2, lng2):
    dlng = radians(lng2 - lng1)
    dlat = radians(lat2 - lat1)
    head = atan2(dlng, dlat) * 180 / 3.14159
    return head % 360


class Command(BaseCommand):
    help = "Simulate bus movement for demo. Moves all active trips along their routes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval", type=int, default=5,
            help="Seconds between position updates (default: 5)",
        )
        parser.add_argument(
            "--speed-multiplier", type=float, default=1.0,
            help="Speed multiplier: 2.0 = 2x faster, 0.5 = 2x slower (default: 1.0)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        multiplier = options["speed_multiplier"]

        self.stdout.write(self.style.MIGRATE_HEADING("=== DEMO SIMULATOR ==="))
        self.stdout.write(f"  Intervalo: {interval}s | Velocidad: {multiplier}x")
        self.stdout.write("  Presione CTRL+C para detener.\n")

        bus_states = self._init_states()
        if not bus_states:
            self.stdout.write(self.style.ERROR("No hay trips activos. Ejecute 'setup_demo' primero."))
            return

        self.stdout.write(self.style.SUCCESS(f"  {len(bus_states)} buses activos\n"))

        try:
            self._run_loop(bus_states, interval, multiplier)
        except KeyboardInterrupt:
            self.stdout.write("\nSimulación detenida.")

    def _init_states(self):
        trips = Trip.objects.filter(
            status=Trip.Status.IN_PROGRESS,
            is_active=True,
        ).select_related("route")

        states = []
        for trip in trips:
            coords = list(
                RouteCoordinate.objects.filter(
                    route=trip.route, is_active=True
                ).order_by("order")
            )

            if len(coords) < 2:
                continue

            points = [(float(c.latitude), float(c.longitude)) for c in coords]
            last_pos = GPSPosition.objects.filter(
                trip=trip, is_active=True
            ).order_by("-recorded_at").first()

            if last_pos:
                start_lat = float(last_pos.latitude)
                start_lng = float(last_pos.longitude)
                best_idx = 0
                best_dist = float("inf")
                for i, (plat, plng) in enumerate(points):
                    d = _haversine(start_lat, start_lng, plat, plng)
                    if d < best_dist:
                        best_dist = d
                        best_idx = i
                current_idx = best_idx
            else:
                current_idx = 0

            states.append({
                "trip": trip,
                "points": points,
                "current_idx": current_idx,
                "step": 0,
                "segment_progress": 0.0,
            })

        return states

    def _run_loop(self, states, interval, multiplier):
        step = 0
        while True:
            now = datetime.now(UTC)

            for state in states:
                state["step"] = step
                lat, lng, speed, heading = self._next_position(state, multiplier)
                GPSPosition.objects.create(
                    trip=state["trip"],
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    speed=round(speed, 2),
                    heading=round(heading, 2),
                    recorded_at=now,
                )

                route = state["trip"].route
                plate = state["trip"].vehicle.plate
                idx = state["current_idx"]
                n = len(state["points"]) - 1
                progress = (idx / n) * 100

                self.stdout.write(
                    f"  [{step:04d}] {route.code} ({plate}): "
                    f"({lat:.6f}, {lng:.6f}) "
                    f"{speed:.0f} km/h | {progress:.0f}%"
                )

            step += 1
            sleep(interval)

    def _next_position(self, state, multiplier):
        points = state["points"]
        idx = state["current_idx"]
        n = len(points)
        step = state["step"]

        if idx >= n - 1:
            state["current_idx"] = 0
            idx = 0

        lat1, lng1 = points[idx]
        lat2, lng2 = points[idx + 1]

        seg_dist = _haversine(lat1, lng1, lat2, lng2)
        base_speed_kmh = 30 + 8 * (step % 4)
        speed_kmh = base_speed_kmh * multiplier

        dist_per_step = (speed_kmh / 3600) * 5
        if seg_dist > 0:
            state["segment_progress"] += dist_per_step / seg_dist
        else:
            state["segment_progress"] = 1.0

        if state["segment_progress"] >= 1.0:
            state["segment_progress"] = 0.0
            state["current_idx"] = min(idx + 1, n - 2)
            idx = state["current_idx"]
            lat1, lng1 = points[idx]
            lat2, lng2 = points[idx + 1]

        t = state["segment_progress"]
        lat = _interpolate(lat1, lat2, t)
        lng = _interpolate(lng1, lng2, t)

        heading = _heading(lat1, lng1, lat2, lng2)

        progress = idx / (n - 1) if n > 1 else 0
        if progress < 0.15:
            speed = speed_kmh * (0.4 + 0.6 * (progress / 0.15))
        elif progress > 0.85:
            speed = speed_kmh * (1.0 - 0.6 * ((progress - 0.85) / 0.15))
        else:
            speed = speed_kmh

        return lat, lng, max(speed, 5), heading
