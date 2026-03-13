from django.db import transaction

from alerts.services import evaluate_traffic_alerts
from traffic.models import Traffic
from vehicles.models import Vehicle


def ingest_camera_payload(validated_data):
    camera = validated_data['camera']
    measured_at = validated_data['measured_at']
    vehicles_data = validated_data.get('vehicles', [])

    with transaction.atomic():
        traffic_record = Traffic.objects.create(
            camera=camera,
            measured_at=measured_at,
            vehicle_count=validated_data['vehicle_count'],
            avg_speed_kph=validated_data['avg_speed_kph'],
            congestion_level=validated_data['congestion_level'],
            occupancy_percent=validated_data['occupancy_percent'],
        )

        vehicle_events = []
        for vehicle_data in vehicles_data:
            vehicle_events.append(
                Vehicle(
                    camera=camera,
                    traffic_record=traffic_record,
                    detected_at=vehicle_data.get('detected_at', measured_at),
                    vehicle_type=vehicle_data['vehicle_type'],
                    plate_number=vehicle_data.get('plate_number', ''),
                    speed_kph=vehicle_data.get('speed_kph'),
                    lane_number=vehicle_data.get('lane_number', 1),
                    is_violation=vehicle_data.get('is_violation', False),
                )
            )

        if vehicle_events:
            Vehicle.objects.bulk_create(vehicle_events)

        camera.last_seen_at = measured_at
        camera.save(update_fields=['last_seen_at', 'updated_at'])

        created_alerts = evaluate_traffic_alerts(traffic_record)

    return {
        'traffic_record': traffic_record,
        'vehicle_events_created': len(vehicle_events),
        'alerts_created': len(created_alerts),
    }
