from django.db import models


class Camera(models.Model):
	class Status(models.TextChoices):
		ONLINE = 'online', 'Online'
		OFFLINE = 'offline', 'Offline'
		MAINTENANCE = 'maintenance', 'Maintenance'

	code = models.CharField(max_length=64, unique=True)
	name = models.CharField(max_length=120)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)
	longitude = models.DecimalField(max_digits=9, decimal_places=6)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONLINE)
	is_active = models.BooleanField(default=True)
	last_seen_at = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['code']

	def __str__(self):
		return f'{self.code} ({self.name})'
