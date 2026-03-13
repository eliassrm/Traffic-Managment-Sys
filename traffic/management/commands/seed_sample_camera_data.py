import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from alerts.models import Alert
from cameras.models import Camera
from traffic.models import Traffic
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = 'Create sample camera, traffic, vehicle, and alert records for frontend testing.'

    def add_arguments(self, parser):
        parser.add_argument('--records-per-camera', type=int, default=24)
        parser.add_argument('--reset', action='store_true')

    def handle(self, *args, **options):
        records_per_camera = max(6, options['records_per_camera'])
        reset = options['reset']
        rng = random.Random(42)

        camera_specs = [
            ('SAMPLE-CAM-001', 'Main Junction', 30.0444, 31.2357),
            ('SAMPLE-CAM-002', 'North Ring', 30.0732, 31.3056),
            ('SAMPLE-CAM-003', 'South Bridge', 29.9716, 31.2231),
        ]

        with transaction.atomic():
            cameras = []
            for code, name, lat, lng in camera_specs:
                camera, _ = Camera.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'latitude': lat,
                        'longitude': lng,
                        'status': Camera.Status.ONLINE,
                        'is_active': True,
                    },
                )
                cameras.append(camera)

            if reset:
                Traffic.objects.filter(camera__in=cameras).delete()
                Alert.objects.filter(camera__in=cameras).delete()

            now = timezone.now()
            inserted_traffic = 0
            inserted_vehicle = 0
            inserted_alerts = 0

            for camera in cameras:
                for i in range(records_per_camera):
                    measured_at = now - timedelta(minutes=(records_per_camera - i) * 5)
                    base_volume = 25 + i + rng.randint(0, 18)
                    occupancy = min(100, max(8, 22 + i * 2 + rng.randint(-6, 10)))
                    speed = max(6, 70 - occupancy * 0.55 + rng.randint(-5, 5))

                    if occupancy >= 88:
                        congestion = Traffic.CongestionLevel.SEVERE
                    elif occupancy >= 70:
                        congestion = Traffic.CongestionLevel.HIGH
                    elif occupancy >= 45:
                        congestion = Traffic.CongestionLevel.MODERATE
                    else:
                        congestion = Traffic.CongestionLevel.LOW

                    traffic = Traffic.objects.create(
                        camera=camera,
                        measured_at=measured_at,
                        vehicle_count=base_volume,
                        avg_speed_kph=round(speed, 2),
                        congestion_level=congestion,
                        occupancy_percent=round(occupancy, 2),
                    )
                    inserted_traffic += 1

                    event_count = rng.randint(1, min(5, max(2, base_volume // 15)))
                    events = []
                    for _ in range(event_count):
                        v_type = rng.choice([item[0] for item in Vehicle.VehicleType.choices])
                        events.append(
                            Vehicle(
                                camera=camera,
                                traffic_record=traffic,
                                detected_at=measured_at,
                                vehicle_type=v_type,
                                lane_number=rng.randint(1, 4),
                                is_violation=rng.random() < 0.08,
                            )
                        )
                    Vehicle.objects.bulk_create(events)
                    inserted_vehicle += len(events)

                    if congestion in (Traffic.CongestionLevel.HIGH, Traffic.CongestionLevel.SEVERE) and rng.random() < 0.18:
                        Alert.objects.create(
                            camera=camera,
                            traffic_record=traffic,
                            title=f'Congestion detected on {camera.code}',
                            description=f'Auto-sampled alert at occupancy {occupancy}%.',
                            source_type=Alert.SourceType.TRAFFIC,
                            source_reference=f'traffic:{traffic.id}',
                            severity=Alert.Severity.CRITICAL if congestion == Traffic.CongestionLevel.SEVERE else Alert.Severity.WARNING,
                            status=Alert.Status.OPEN,
                            triggered_at=timezone.now(),
                        )
                        inserted_alerts += 1

                camera.last_seen_at = now
                camera.save(update_fields=['last_seen_at', 'updated_at'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed complete: {len(cameras)} camera(s), {inserted_traffic} traffic rows, '
                f'{inserted_vehicle} vehicle events, {inserted_alerts} alert(s).'
            )
        )
