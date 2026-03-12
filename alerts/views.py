from rest_framework import viewsets

from .models import Alert
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
	queryset = Alert.objects.select_related('camera', 'traffic_record').all()
	serializer_class = AlertSerializer
