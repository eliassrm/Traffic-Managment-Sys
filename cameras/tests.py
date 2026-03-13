from django.contrib.auth.models import Permission, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cameras.models import Camera
from traffic.models import Traffic
from vehicles.models import Vehicle


class CameraIngestionTests(APITestCase):
	def setUp(self):
		self.url = reverse('camera-ingest')
		self.user = User.objects.create_user(username='operator1', password='testpass123')
		self.user.user_permissions.add(Permission.objects.get(codename='add_traffic'))
		self.user.user_permissions.add(Permission.objects.get(codename='add_vehicle'))

		self.camera = Camera.objects.create(
			code='CAM-001',
			name='Main Junction',
			latitude=30.044400,
			longitude=31.235700,
			status='online',
			is_active=True,
		)

	def test_ingestion_creates_traffic_and_vehicle_records(self):
		self.client.force_authenticate(user=self.user)

		payload = {
			'camera_code': 'CAM-001',
			'measured_at': '2026-03-13T10:00:00Z',
			'vehicle_count': 2,
			'avg_speed_kph': '42.50',
			'congestion_level': 'moderate',
			'occupancy_percent': '58.20',
			'vehicles': [
				{
					'vehicle_type': 'car',
					'lane_number': 1,
					'is_violation': False,
				},
				{
					'vehicle_type': 'bus',
					'lane_number': 2,
					'is_violation': True,
				},
			],
		}

		response = self.client.post(self.url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Traffic.objects.count(), 1)
		self.assertEqual(Vehicle.objects.count(), 2)
		self.assertEqual(response.data['vehicle_events_created'], 2)

	def test_ingestion_rejects_unknown_camera(self):
		self.client.force_authenticate(user=self.user)

		payload = {
			'camera_code': 'CAM-404',
			'measured_at': '2026-03-13T10:00:00Z',
			'vehicle_count': 1,
			'avg_speed_kph': '31.00',
			'congestion_level': 'low',
			'occupancy_percent': '25.00',
		}

		response = self.client.post(self.url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('camera_code', response.data)

	def test_ingestion_requires_permissions(self):
		no_perm_user = User.objects.create_user(username='viewer1', password='testpass123')
		self.client.force_authenticate(user=no_perm_user)

		payload = {
			'camera_code': 'CAM-001',
			'measured_at': '2026-03-13T10:00:00Z',
			'vehicle_count': 0,
			'avg_speed_kph': '15.00',
			'congestion_level': 'low',
			'occupancy_percent': '10.00',
		}

		response = self.client.post(self.url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
