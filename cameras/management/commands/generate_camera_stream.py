import math
import random
import time
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from cameras.models import Camera
from cameras.services import ingest_camera_payload
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = 'Generate synthetic video-camera-like traffic data and ingest it into the app.'

    def add_arguments(self, parser):
        parser.add_argument('--camera-code', type=str, help='Camera code to target. Uses first active camera if omitted.')
        parser.add_argument('--samples', type=int, default=24, help='Number of generated samples.')
        parser.add_argument('--interval-seconds', type=int, default=5, help='Seconds between samples.')
        parser.add_argument(
            '--mode',
            type=str,
            default='normal',
            choices=['calm', 'normal', 'rush', 'chaos'],
            help='Traffic intensity profile.',
        )
        parser.add_argument('--realtime', action='store_true', help='Sleep between samples to emulate real stream speed.')
        parser.add_argument('--seed', type=int, default=1337, help='Random seed for reproducible generation.')

    def handle(self, *args, **options):
        camera = self._get_camera(options.get('camera_code'))
        samples = max(1, options['samples'])
        interval = max(1, options['interval_seconds'])
        mode = options['mode']
        realtime = options['realtime']
        rng = random.Random(options['seed'])

        start_time = timezone.now()
        total_vehicles = 0
        total_alerts = 0

        self.stdout.write(
            self.style.WARNING(
                f'Starting stream generator for camera={camera.code}, samples={samples}, mode={mode}, interval={interval}s.'
            )
        )

        for i in range(samples):
            measured_at = timezone.now() if realtime else (start_time + timedelta(seconds=i * interval))
            payload = self._build_payload(camera, measured_at, i, mode, rng)
            result = ingest_camera_payload(payload)

            total_vehicles += payload['vehicle_count']
            total_alerts += result['alerts_created']

            self.stdout.write(
                f"[{i + 1:03d}/{samples:03d}] "
                f"at {measured_at.isoformat()} | "
                f"vehicles={payload['vehicle_count']}, speed={payload['avg_speed_kph']}, "
                f"occupancy={payload['occupancy_percent']}%, level={payload['congestion_level']} "
                f"=> traffic_id={result['traffic_record'].id}, alerts={result['alerts_created']}"
            )

            if realtime and i < samples - 1:
                time.sleep(interval)

        self.stdout.write(
            self.style.SUCCESS(
                f'Completed stream generation. Samples={samples}, total_vehicle_count={total_vehicles}, '
                f'alerts_created={total_alerts}.'
            )
        )

    def _get_camera(self, camera_code):
        if camera_code:
            try:
                return Camera.objects.get(code=camera_code, is_active=True)
            except Camera.DoesNotExist as exc:
                raise CommandError(f'Active camera with code "{camera_code}" does not exist.') from exc

        camera = Camera.objects.filter(is_active=True).order_by('code').first()
        if not camera:
            raise CommandError('No active cameras found. Create one first or run seed_sample_camera_data.')
        return camera

    def _build_payload(self, camera, measured_at, step, mode, rng):
        base_map = {
            'calm': 16,
            'normal': 36,
            'rush': 70,
            'chaos': 92,
        }
        variance_map = {
            'calm': 6,
            'normal': 12,
            'rush': 16,
            'chaos': 24,
        }

        base = base_map[mode]
        variance = variance_map[mode]

        wave = math.sin(step / 3.0) * variance * 0.75
        burst = variance * 0.8 if (mode in ('rush', 'chaos') and step % 7 == 0) else 0
        vehicle_count = int(max(0, base + wave + burst + rng.randint(-variance, variance)))

        occupancy_percent = round(min(100, max(5, 12 + vehicle_count * 0.85 + rng.randint(-8, 8))), 2)
        avg_speed = round(max(5, 84 - occupancy_percent * 0.72 + rng.randint(-5, 5)), 2)

        if occupancy_percent >= 88:
            congestion_level = 'severe'
        elif occupancy_percent >= 68:
            congestion_level = 'high'
        elif occupancy_percent >= 42:
            congestion_level = 'moderate'
        else:
            congestion_level = 'low'

        vehicle_events = self._build_vehicle_events(vehicle_count, measured_at, avg_speed, rng)

        return {
            'camera': camera,
            'measured_at': measured_at,
            'vehicle_count': vehicle_count,
            'avg_speed_kph': avg_speed,
            'congestion_level': congestion_level,
            'occupancy_percent': occupancy_percent,
            'vehicles': vehicle_events,
        }

    def _build_vehicle_events(self, vehicle_count, measured_at, avg_speed, rng):
        if vehicle_count <= 0:
            return []

        max_events = min(vehicle_count, 12)
        min_events = min(max_events, 2)
        event_count = rng.randint(min_events, max_events)

        vehicle_types = [item[0] for item in Vehicle.VehicleType.choices]
        lane_choices = [1, 2, 3, 4]

        events = []
        for _ in range(event_count):
            events.append(
                {
                    'vehicle_type': rng.choice(vehicle_types),
                    'detected_at': measured_at,
                    'lane_number': rng.choice(lane_choices),
                    'speed_kph': round(max(0, avg_speed + rng.randint(-15, 10)), 2),
                    'is_violation': rng.random() < 0.06,
                }
            )

        return events
