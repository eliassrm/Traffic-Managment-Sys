from rest_framework import serializers

from .models import Camera
from .services import ingest_camera_payload
from traffic.models import Traffic
from vehicles.models import Vehicle


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = '__all__'


class VehicleIngestionSerializer(serializers.Serializer):
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VehicleType.choices)
    detected_at = serializers.DateTimeField(required=False)
    plate_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    speed_kph = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, min_value=0)
    lane_number = serializers.IntegerField(required=False, min_value=1)
    is_violation = serializers.BooleanField(required=False, default=False)


class CameraIngestionSerializer(serializers.Serializer):
    camera_code = serializers.CharField(max_length=64)
    measured_at = serializers.DateTimeField()
    vehicle_count = serializers.IntegerField(min_value=0)
    avg_speed_kph = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=300)
    congestion_level = serializers.ChoiceField(choices=Traffic.CongestionLevel.choices)
    occupancy_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100)
    vehicles = VehicleIngestionSerializer(many=True, required=False, default=list)

    def validate_camera_code(self, value):
        try:
            camera = Camera.objects.get(code=value, is_active=True)
        except Camera.DoesNotExist:
            raise serializers.ValidationError('Active camera with this code was not found.')

        self.context['camera'] = camera
        return value

    def validate(self, attrs):
        vehicles_count = len(attrs.get('vehicles', []))
        if vehicles_count > attrs['vehicle_count']:
            raise serializers.ValidationError(
                {'vehicle_count': 'vehicle_count cannot be less than number of vehicle events.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data['camera'] = self.context['camera']
        validated_data.pop('camera_code', None)
        return ingest_camera_payload(validated_data)
