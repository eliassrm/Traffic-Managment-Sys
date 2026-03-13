from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from cameras.models import Camera
from traffic.models import TrafficPrediction


class ApiIntegrationFlowTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='integration_user', password='pass123456')

		required_permissions = [
			'add_traffic',
			'add_vehicle',
			'add_trafficprediction',
			'view_alert',
		]
		for codename in required_permissions:
			self.user.user_permissions.add(Permission.objects.get(codename=codename))

		self.camera = Camera.objects.create(
			code='CAM-INTEG-1',
			name='Integration Camera',
			latitude=30.110000,
			longitude=31.210000,
			status='online',
			is_active=True,
		)

	def _login_and_get_auth_header(self):
		response = self.client.post(
			'/api/auth/token/',
			{'username': 'integration_user', 'password': 'pass123456'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		access_token = response.data['access']
		return {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

	def test_full_workflow_ingestion_prediction_and_alert_access(self):
		headers = self._login_and_get_auth_header()

		me_response = self.client.get('/api/auth/me/', **headers)
		self.assertEqual(me_response.status_code, status.HTTP_200_OK)
		self.assertEqual(me_response.data['username'], 'integration_user')

		base_time = timezone.now() - timedelta(minutes=30)
		for idx in range(6):
			payload = {
				'camera_code': 'CAM-INTEG-1',
				'measured_at': (base_time + timedelta(minutes=idx * 5)).isoformat().replace('+00:00', 'Z'),
				'vehicle_count': 80 + idx,
				'avg_speed_kph': '18.00',
				'congestion_level': 'high',
				'occupancy_percent': '88.00',
				'vehicles': [
					{'vehicle_type': 'car', 'lane_number': 1, 'is_violation': False},
					{'vehicle_type': 'bus', 'lane_number': 2, 'is_violation': False},
				],
			}
			ingest_response = self.client.post('/api/cameras/ingest/', payload, format='json', **headers)
			self.assertEqual(ingest_response.status_code, status.HTTP_201_CREATED)

		prediction_response = self.client.post(
			'/api/traffic/predictions/generate/',
			{'camera_code': 'CAM-INTEG-1', 'horizon_minutes': 10},
			format='json',
			**headers,
		)
		self.assertEqual(prediction_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(prediction_response.data['camera_code'], 'CAM-INTEG-1')
		self.assertGreaterEqual(TrafficPrediction.objects.count(), 1)

		alerts_response = self.client.get('/api/alerts/', **headers)
		self.assertEqual(alerts_response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(alerts_response.data), 1)
