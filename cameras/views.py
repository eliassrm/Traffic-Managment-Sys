from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import Camera
from .permissions import CanIngestCameraData
from .serializers import CameraIngestionSerializer, CameraSerializer


class CameraViewSet(viewsets.ModelViewSet):
	queryset = Camera.objects.all()
	serializer_class = CameraSerializer
	permission_classes = [DjangoModelPermissions]


class CameraIngestionView(APIView):
	permission_classes = [CanIngestCameraData]

	def post(self, request):
		serializer = CameraIngestionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		result = serializer.save()

		return Response(
			{
				'message': 'Camera payload processed successfully.',
				'traffic_record_id': result['traffic_record'].id,
				'vehicle_events_created': result['vehicle_events_created'],
				'alerts_created': result['alerts_created'],
			},
			status=status.HTTP_201_CREATED,
		)
