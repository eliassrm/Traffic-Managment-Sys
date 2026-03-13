from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from cameras.models import Camera

from .models import Traffic, TrafficPrediction


class TrafficPredictionTests(APITestCase):
	def setUp(self):
		self.camera = Camera.objects.create(
			code='CAM-PRED-1',
			name='Prediction Camera',
			latitude=30.000100,
			longitude=31.000100,
			status='online',
			is_active=True,
		)

		base_time = timezone.now() - timedelta(minutes=35)
		congestion_levels = ['low', 'moderate', 'moderate', 'high', 'moderate', 'high', 'high']
		for idx, level in enumerate(congestion_levels):
			Traffic.objects.create(
				camera=self.camera,
				measured_at=base_time + timedelta(minutes=idx * 5),
				vehicle_count=25 + idx,
				avg_speed_kph=55 - idx,
				congestion_level=level,
				occupancy_percent=40 + idx,
			)

		self.generate_url = reverse('traffic-prediction-generate')
		self.user = User.objects.create_user(username='predictor1', password='pass123456')
		self.user.user_permissions.add(Permission.objects.get(codename='add_trafficprediction'))

	def test_generate_prediction_for_single_camera(self):
		self.client.force_authenticate(user=self.user)
		payload = {'camera_code': 'CAM-PRED-1', 'horizon_minutes': 10}

		response = self.client.post(self.generate_url, payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(TrafficPrediction.objects.count(), 1)
		self.assertEqual(response.data['camera_code'], 'CAM-PRED-1')

	def test_generate_prediction_requires_permission(self):
		no_perm_user = User.objects.create_user(username='viewer2', password='pass123456')
		self.client.force_authenticate(user=no_perm_user)

		response = self.client.post(self.generate_url, {'camera_code': 'CAM-PRED-1'}, format='json')

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_generate_prediction_for_all_cameras(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.post(self.generate_url, {'horizon_minutes': 5}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(response.data['generated_count'], 1)
