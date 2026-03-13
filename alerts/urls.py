from rest_framework.routers import DefaultRouter

from .views import AlertNotificationViewSet, AlertRuleViewSet, AlertViewSet

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'alert-rules', AlertRuleViewSet, basename='alert-rule')
router.register(r'alert-notifications', AlertNotificationViewSet, basename='alert-notification')

urlpatterns = router.urls
