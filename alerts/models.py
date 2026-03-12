from django.db import models


class Alert(models.Model):
	class Severity(models.TextChoices):
		INFO = 'info', 'Info'
		WARNING = 'warning', 'Warning'
		CRITICAL = 'critical', 'Critical'

	class Status(models.TextChoices):
		OPEN = 'open', 'Open'
		ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
		RESOLVED = 'resolved', 'Resolved'

	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='alerts')
	traffic_record = models.ForeignKey(
		'traffic.Traffic',
		on_delete=models.SET_NULL,
		related_name='alerts',
		blank=True,
		null=True,
	)
	title = models.CharField(max_length=150)
	description = models.TextField(blank=True)
	severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
	triggered_at = models.DateTimeField(db_index=True)
	resolved_at = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-triggered_at']
		indexes = [
			models.Index(fields=['status', 'severity', '-triggered_at']),
		]

	def __str__(self):
		return f'{self.severity.upper()} - {self.title}'
