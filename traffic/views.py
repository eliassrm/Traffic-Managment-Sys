from rest_framework import viewsets

from .models import Traffic
from .serializers import TrafficSerializer


class TrafficViewSet(viewsets.ModelViewSet):
	queryset = Traffic.objects.select_related('camera').all()
	serializer_class = TrafficSerializer
