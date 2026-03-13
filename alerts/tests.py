from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from cameras.models import Camera
from traffic.models import Traffic, TrafficPrediction

from .models import Alert, AlertNotification, AlertRule
from .services import evaluate_prediction_alerts, evaluate_traffic_alerts


class AlertSystemTests(APITestCase):
	def setUp(self):
		self.camera = Camera.objects.create(
			code='CAM-ALERT-1',
			name='Alert Camera',
			latitude=30.010000,
			longitude=31.010000,
			status='online',
			is_active=True,
		)

		self.user = User.objects.create_user(username='alert_admin', password='pass123456')
		self.user.user_permissions.add(Permission.objects.get(codename='add_alert'))
		self.user.user_permissions.add(Permission.objects.get(codename='change_alert'))
		self.user.user_permissions.add(Permission.objects.get(codename='view_alert'))

	def test_traffic_threshold_generates_alert_and_notification(self):
		rule = AlertRule.objects.create(
			name='Traffic Test Rule',
			rule_type=AlertRule.RuleType.TRAFFIC,
			severity=Alert.Severity.WARNING,
			max_vehicle_count=10,
			notification_channels=['console'],
			is_active=True,
		)

		traffic = Traffic.objects.create(
			camera=self.camera,
			measured_at=timezone.now(),
			vehicle_count=20,
			avg_speed_kph=40,
			congestion_level='moderate',
			occupancy_percent=55,
		)

		alerts = evaluate_traffic_alerts(traffic)

		self.assertEqual(len(alerts), 1)
		self.assertEqual(alerts[0].rule, rule)
		self.assertEqual(AlertNotification.objects.filter(alert=alerts[0]).count(), 1)

	def test_prediction_threshold_generates_alert(self):
		AlertRule.objects.create(
			name='Prediction Test Rule',
			rule_type=AlertRule.RuleType.PREDICTION,
			severity=Alert.Severity.CRITICAL,
			congestion_levels=['severe'],
			min_prediction_confidence=50,
			notification_channels=['console'],
			is_active=True,
		)

		base_traffic = Traffic.objects.create(
			camera=self.camera,
			measured_at=timezone.now() - timedelta(minutes=5),
			vehicle_count=45,
			avg_speed_kph=22,
			congestion_level='high',
			occupancy_percent=75,
		)

		prediction = TrafficPrediction.objects.create(
			camera=self.camera,
			based_on_record=base_traffic,
			predicted_for=timezone.now() + timedelta(minutes=5),
			horizon_minutes=5,
			predicted_congestion_level='severe',
			confidence=80,
			predicted_vehicle_count=95,
			predicted_avg_speed_kph=12,
			predicted_occupancy_percent=92,
			transition_probabilities={'severe': 80.0},
		)

		alerts = evaluate_prediction_alerts(prediction)

		self.assertGreaterEqual(len(alerts), 1)
		self.assertTrue(all(item.source_type == Alert.SourceType.PREDICTION for item in alerts))

	def test_alert_acknowledge_and_resolve_actions(self):
		alert = Alert.objects.create(
			camera=self.camera,
			title='Test alert',
			description='desc',
			severity=Alert.Severity.WARNING,
			status=Alert.Status.OPEN,
			triggered_at=timezone.now(),
		)

		self.client.force_authenticate(user=self.user)

		acknowledge_url = reverse('alert-acknowledge', kwargs={'pk': alert.id})
		resolve_url = reverse('alert-resolve', kwargs={'pk': alert.id})

		response_ack = self.client.post(acknowledge_url, {}, format='json')
		self.assertEqual(response_ack.status_code, status.HTTP_200_OK)

		response_resolve = self.client.post(resolve_url, {}, format='json')
		self.assertEqual(response_resolve.status_code, status.HTTP_200_OK)

		alert.refresh_from_db()
		self.assertEqual(alert.status, Alert.Status.RESOLVED)
		self.assertIsNotNone(alert.resolved_at)
