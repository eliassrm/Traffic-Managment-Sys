from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from .models import Camera
from .serializers import CameraSerializer


class CameraViewSet(viewsets.ModelViewSet):
	queryset = Camera.objects.all()
	serializer_class = CameraSerializer
	permission_classes = [DjangoModelPermissions]
