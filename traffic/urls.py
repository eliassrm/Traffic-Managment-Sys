from rest_framework.routers import DefaultRouter

from .views import TrafficViewSet

router = DefaultRouter()
router.register(r'traffic', TrafficViewSet, basename='traffic')

urlpatterns = router.urls
