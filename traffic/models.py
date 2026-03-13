from django.db import models


class Traffic(models.Model):
	class CongestionLevel(models.TextChoices):
		LOW = 'low', 'Low'
		MODERATE = 'moderate', 'Moderate'
		HIGH = 'high', 'High'
		SEVERE = 'severe', 'Severe'

	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='traffic_records')
	measured_at = models.DateTimeField(db_index=True)
	vehicle_count = models.PositiveIntegerField(default=0)
	avg_speed_kph = models.DecimalField(max_digits=5, decimal_places=2)
	congestion_level = models.CharField(
		max_length=20,
		choices=CongestionLevel.choices,
		default=CongestionLevel.LOW,
		db_index=True,
	)
	occupancy_percent = models.DecimalField(max_digits=5, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-measured_at']
		indexes = [
			models.Index(fields=['camera', '-measured_at']),
		]

	def __str__(self):
		return f'{self.camera.code} @ {self.measured_at:%Y-%m-%d %H:%M:%S}'


class TrafficPrediction(models.Model):
	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='predictions')
	based_on_record = models.ForeignKey(
		Traffic,
		on_delete=models.SET_NULL,
		related_name='generated_predictions',
		blank=True,
		null=True,
	)
	generated_at = models.DateTimeField(auto_now_add=True)
	predicted_for = models.DateTimeField(db_index=True)
	horizon_minutes = models.PositiveIntegerField(default=5)
	predicted_congestion_level = models.CharField(max_length=20, choices=Traffic.CongestionLevel.choices)
	confidence = models.DecimalField(max_digits=5, decimal_places=2)
	predicted_vehicle_count = models.PositiveIntegerField()
	predicted_avg_speed_kph = models.DecimalField(max_digits=6, decimal_places=2)
	predicted_occupancy_percent = models.DecimalField(max_digits=5, decimal_places=2)
	transition_probabilities = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['-predicted_for', '-generated_at']
		indexes = [
			models.Index(fields=['camera', '-predicted_for']),
		]

	def __str__(self):
		return f'Prediction for {self.camera.code} at {self.predicted_for:%Y-%m-%d %H:%M:%S}'
