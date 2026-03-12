from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
	queryset = Vehicle.objects.select_related('camera', 'traffic_record').all()
	serializer_class = VehicleSerializer
	permission_classes = [DjangoModelPermissions]
