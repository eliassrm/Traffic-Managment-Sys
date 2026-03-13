from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Traffic, TrafficPrediction
from .permissions import CanGenerateTrafficPrediction
from .prediction_service import PredictionInsufficientDataError, generate_prediction_for_camera, generate_predictions_for_all_cameras
from .serializers import PredictionGenerateSerializer, TrafficPredictionSerializer, TrafficSerializer


class TrafficViewSet(viewsets.ModelViewSet):
	queryset = Traffic.objects.select_related('camera').all()
	serializer_class = TrafficSerializer
	permission_classes = [DjangoModelPermissions]


class TrafficPredictionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TrafficPrediction.objects.select_related('camera', 'based_on_record').all()
	serializer_class = TrafficPredictionSerializer
	permission_classes = [DjangoModelPermissions]


class TrafficPredictionGenerateView(APIView):
	permission_classes = [CanGenerateTrafficPrediction]

	def post(self, request):
		serializer = PredictionGenerateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		horizon_minutes = serializer.validated_data.get('horizon_minutes', 5)
		camera = serializer.context.get('camera')

		if camera is not None:
			try:
				prediction = generate_prediction_for_camera(camera, horizon_minutes=horizon_minutes)
			except PredictionInsufficientDataError as exc:
				return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

			return Response(
				TrafficPredictionSerializer(prediction).data,
				status=status.HTTP_201_CREATED,
			)

		predictions = generate_predictions_for_all_cameras(horizon_minutes=horizon_minutes)
		return Response(
			{
				'generated_count': len(predictions),
				'predictions': TrafficPredictionSerializer(predictions, many=True).data,
			},
			status=status.HTTP_200_OK,
		)
