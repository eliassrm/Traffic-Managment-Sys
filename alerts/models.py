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

	class SourceType(models.TextChoices):
		TRAFFIC = 'traffic', 'Traffic'
		PREDICTION = 'prediction', 'Prediction'
		SYSTEM = 'system', 'System'

	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='alerts')
	traffic_record = models.ForeignKey(
		'traffic.Traffic',
		on_delete=models.SET_NULL,
		related_name='alerts',
		blank=True,
		null=True,
	)
	prediction_record = models.ForeignKey(
		'traffic.TrafficPrediction',
		on_delete=models.SET_NULL,
		related_name='alerts',
		blank=True,
		null=True,
	)
	rule = models.ForeignKey(
		'alerts.AlertRule',
		on_delete=models.SET_NULL,
		related_name='generated_alerts',
		blank=True,
		null=True,
	)
	title = models.CharField(max_length=150)
	description = models.TextField(blank=True)
	source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.SYSTEM, db_index=True)
	source_reference = models.CharField(max_length=64, blank=True, db_index=True)
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
			models.Index(fields=['camera', 'status', '-triggered_at']),
		]

	def __str__(self):
		return f'{self.severity.upper()} - {self.title}'


class AlertRule(models.Model):
	class RuleType(models.TextChoices):
		TRAFFIC = 'traffic', 'Traffic'
		PREDICTION = 'prediction', 'Prediction'

	name = models.CharField(max_length=120, unique=True)
	is_active = models.BooleanField(default=True)
	rule_type = models.CharField(max_length=20, choices=RuleType.choices)
	camera = models.ForeignKey('cameras.Camera', on_delete=models.CASCADE, related_name='alert_rules', blank=True, null=True)
	severity = models.CharField(max_length=20, choices=Alert.Severity.choices, default=Alert.Severity.WARNING)
	max_vehicle_count = models.PositiveIntegerField(blank=True, null=True)
	max_occupancy_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	min_avg_speed_kph = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
	congestion_levels = models.JSONField(default=list, blank=True)
	min_prediction_confidence = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
	notification_channels = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']
		indexes = [
			models.Index(fields=['rule_type', 'is_active']),
		]

	def __str__(self):
		return self.name


class AlertNotification(models.Model):
	class Channel(models.TextChoices):
		EMAIL = 'email', 'Email'
		PUSH = 'push', 'Push'
		CONSOLE = 'console', 'Console'

	class DeliveryStatus(models.TextChoices):
		QUEUED = 'queued', 'Queued'
		SENT = 'sent', 'Sent'
		FAILED = 'failed', 'Failed'

	alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='notifications')
	channel = models.CharField(max_length=20, choices=Channel.choices)
	status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.QUEUED)
	message = models.TextField(blank=True)
	error = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	delivered_at = models.DateTimeField(blank=True, null=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['channel', 'status', '-created_at']),
		]

	def __str__(self):
		return f'{self.channel} - {self.status} ({self.alert_id})'
