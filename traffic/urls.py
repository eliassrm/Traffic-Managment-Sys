from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TrafficPredictionGenerateView, TrafficPredictionViewSet, TrafficViewSet

router = DefaultRouter()
router.register(r'traffic', TrafficViewSet, basename='traffic')
router.register(r'traffic/predictions', TrafficPredictionViewSet, basename='traffic-prediction')

urlpatterns = [
	path('traffic/predictions/generate/', TrafficPredictionGenerateView.as_view(), name='traffic-prediction-generate'),
	*router.urls,
]
