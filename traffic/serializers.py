from rest_framework import serializers

from cameras.models import Camera
from .models import Traffic
from .models import TrafficPrediction


class TrafficSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traffic
        fields = '__all__'


class TrafficPredictionSerializer(serializers.ModelSerializer):
    camera_code = serializers.CharField(source='camera.code', read_only=True)

    class Meta:
        model = TrafficPrediction
        fields = '__all__'


class PredictionGenerateSerializer(serializers.Serializer):
    camera_code = serializers.CharField(required=False, max_length=64)
    horizon_minutes = serializers.IntegerField(required=False, default=5, min_value=1, max_value=180)

    def validate_camera_code(self, value):
        try:
            camera = Camera.objects.get(code=value, is_active=True)
        except Camera.DoesNotExist:
            raise serializers.ValidationError('Active camera with this code was not found.')

        self.context['camera'] = camera
        return value
