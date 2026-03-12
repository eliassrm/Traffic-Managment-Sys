from django.db import models


class Vehicle(models.Model):
	class VehicleType(models.TextChoices):
		CAR = 'car', 'Car'
		BUS = 'bus', 'Bus'
		TRUCK = 'truck', 'Truck'
		MOTORBIKE = 'motorbike', 'Motorbike'
		EMERGENCY = 'emergency', 'Emergency'
		OTHER = 'other', 'Other'

	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='vehicle_events')
	traffic_record = models.ForeignKey(
		'traffic.Traffic',
		on_delete=models.SET_NULL,
		related_name='vehicle_events',
		blank=True,
		null=True,
	)
	detected_at = models.DateTimeField(db_index=True)
	vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, db_index=True)
	plate_number = models.CharField(max_length=20, blank=True)
	speed_kph = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	lane_number = models.PositiveSmallIntegerField(default=1)
	is_violation = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-detected_at']
		indexes = [
			models.Index(fields=['camera', '-detected_at']),
		]

	def __str__(self):
		return f'{self.vehicle_type} on {self.camera.code} @ {self.detected_at:%Y-%m-%d %H:%M:%S}'
