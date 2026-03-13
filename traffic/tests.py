from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from cameras.models import Camera

from .models import Traffic, TrafficArchive, TrafficPrediction


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


class TrafficArchivalCommandTests(APITestCase):
	def setUp(self):
		self.camera = Camera.objects.create(
			code='CAM-ARCH-1',
			name='Archive Camera',
			latitude=30.100000,
			longitude=31.100000,
			status='online',
			is_active=True,
		)

		old_time = timezone.now() - timedelta(days=45)
		recent_time = timezone.now() - timedelta(days=3)

		self.old_record = Traffic.objects.create(
			camera=self.camera,
			measured_at=old_time,
			vehicle_count=20,
			avg_speed_kph=50,
			congestion_level='low',
			occupancy_percent=30,
		)
		self.recent_record = Traffic.objects.create(
			camera=self.camera,
			measured_at=recent_time,
			vehicle_count=40,
			avg_speed_kph=28,
			congestion_level='high',
			occupancy_percent=70,
		)

	def test_archive_command_dry_run(self):
		stdout = StringIO()
		call_command('archive_traffic_data', older_than_days=30, dry_run=True, stdout=stdout)

		self.assertEqual(Traffic.objects.count(), 2)
		self.assertEqual(TrafficArchive.objects.count(), 0)

	def test_archive_command_moves_old_records(self):
		stdout = StringIO()
		call_command('archive_traffic_data', older_than_days=30, batch_size=10, stdout=stdout)

		self.assertEqual(Traffic.objects.count(), 1)
		self.assertEqual(TrafficArchive.objects.count(), 1)
		archived = TrafficArchive.objects.first()
		self.assertEqual(archived.source_record_id, self.old_record.id)
