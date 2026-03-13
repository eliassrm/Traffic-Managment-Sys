from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework import status

from .models import Alert, AlertNotification, AlertRule
from .serializers import AlertNotificationSerializer, AlertRuleSerializer, AlertSerializer
from .services import mark_alert_acknowledged, mark_alert_resolved


class AlertViewSet(viewsets.ModelViewSet):
	queryset = Alert.objects.select_related('camera', 'traffic_record').all()
	serializer_class = AlertSerializer
	permission_classes = [DjangoModelPermissions]

	@action(detail=True, methods=['post'])
	def acknowledge(self, request, pk=None):
		alert = self.get_object()
		mark_alert_acknowledged(alert)
		return Response(self.get_serializer(alert).data, status=status.HTTP_200_OK)

	@action(detail=True, methods=['post'])
	def resolve(self, request, pk=None):
		alert = self.get_object()
		mark_alert_resolved(alert)
		return Response(self.get_serializer(alert).data, status=status.HTTP_200_OK)


class AlertRuleViewSet(viewsets.ModelViewSet):
	queryset = AlertRule.objects.select_related('camera').all()
	serializer_class = AlertRuleSerializer
	permission_classes = [DjangoModelPermissions]


class AlertNotificationViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AlertNotification.objects.select_related('alert').all()
	serializer_class = AlertNotificationSerializer
	permission_classes = [DjangoModelPermissions]
