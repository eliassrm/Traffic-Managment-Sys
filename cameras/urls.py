from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CameraIngestionView, CameraViewSet

router = DefaultRouter()
router.register(r'cameras', CameraViewSet, basename='camera')

urlpatterns = [
	path('cameras/ingest/', CameraIngestionView.as_view(), name='camera-ingest'),
	*router.urls,
]
