from django.db.models import Q
from django.utils import timezone

from .models import Alert, AlertNotification, AlertRule


def ensure_default_alert_rules():
    defaults = [
        {
            'name': 'Default Traffic Overflow',
            'rule_type': AlertRule.RuleType.TRAFFIC,
            'severity': Alert.Severity.WARNING,
            'max_vehicle_count': 70,
            'max_occupancy_percent': 80,
            'min_avg_speed_kph': 20,
            'congestion_levels': ['high', 'severe'],
            'notification_channels': ['console'],
        },
        {
            'name': 'Default Prediction Overflow',
            'rule_type': AlertRule.RuleType.PREDICTION,
            'severity': Alert.Severity.CRITICAL,
            'max_vehicle_count': 90,
            'max_occupancy_percent': 90,
            'min_avg_speed_kph': 15,
            'congestion_levels': ['severe'],
            'min_prediction_confidence': 60,
            'notification_channels': ['console'],
        },
    ]

    for rule in defaults:
        AlertRule.objects.get_or_create(name=rule['name'], defaults=rule)


def _rule_applies_to_camera(rule, camera):
    return rule.camera_id is None or rule.camera_id == camera.id


def _evaluate_conditions(rule, vehicle_count, occupancy_percent, avg_speed_kph, congestion_level, confidence=None):
    matched_reasons = []

    if rule.max_vehicle_count is not None and vehicle_count >= rule.max_vehicle_count:
        matched_reasons.append(f'vehicle_count={vehicle_count} >= {rule.max_vehicle_count}')

    if rule.max_occupancy_percent is not None and occupancy_percent >= rule.max_occupancy_percent:
        matched_reasons.append(
            f'occupancy_percent={occupancy_percent} >= {rule.max_occupancy_percent}'
        )

    if rule.min_avg_speed_kph is not None and avg_speed_kph <= rule.min_avg_speed_kph:
        matched_reasons.append(f'avg_speed_kph={avg_speed_kph} <= {rule.min_avg_speed_kph}')

    if rule.congestion_levels and congestion_level in rule.congestion_levels:
        matched_reasons.append(f'congestion_level={congestion_level} in {rule.congestion_levels}')

    if confidence is not None and rule.min_prediction_confidence is not None and confidence >= rule.min_prediction_confidence:
        matched_reasons.append(f'confidence={confidence} >= {rule.min_prediction_confidence}')

    return matched_reasons


def _send_notifications(alert, channels):
    channels = channels or ['console']
    notifications = []
    for channel in channels:
        notification = AlertNotification.objects.create(
            alert=alert,
            channel=channel,
            status=AlertNotification.DeliveryStatus.QUEUED,
            message=f'Alert {alert.id}: {alert.title}',
        )

        if channel == AlertNotification.Channel.CONSOLE:
            notification.status = AlertNotification.DeliveryStatus.SENT
            notification.delivered_at = timezone.now()
            notification.save(update_fields=['status', 'delivered_at'])
        elif channel in (AlertNotification.Channel.EMAIL, AlertNotification.Channel.PUSH):
            notification.status = AlertNotification.DeliveryStatus.SENT
            notification.delivered_at = timezone.now()
            notification.save(update_fields=['status', 'delivered_at'])
        else:
            notification.status = AlertNotification.DeliveryStatus.FAILED
            notification.error = 'Unsupported channel.'
            notification.save(update_fields=['status', 'error'])

        notifications.append(notification)

    return notifications


def _get_open_duplicate(camera, rule, source_type, source_reference):
    return Alert.objects.filter(
        camera=camera,
        rule=rule,
        source_type=source_type,
        source_reference=source_reference,
        status__in=[Alert.Status.OPEN, Alert.Status.ACKNOWLEDGED],
    ).first()


def _create_alert(camera, rule, source_type, source_reference, title, description, traffic_record=None, prediction_record=None):
    duplicate = _get_open_duplicate(camera, rule, source_type, source_reference)
    if duplicate is not None:
        return duplicate, False

    alert = Alert.objects.create(
        camera=camera,
        traffic_record=traffic_record,
        prediction_record=prediction_record,
        rule=rule,
        title=title,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        severity=rule.severity,
        triggered_at=timezone.now(),
    )
    _send_notifications(alert, rule.notification_channels)
    return alert, True


def evaluate_traffic_alerts(traffic_record):
    ensure_default_alert_rules()
    rules = AlertRule.objects.filter(is_active=True, rule_type=AlertRule.RuleType.TRAFFIC).filter(
        Q(camera__isnull=True) | Q(camera=traffic_record.camera)
    )

    created_alerts = []
    for rule in rules:
        if not _rule_applies_to_camera(rule, traffic_record.camera):
            continue

        reasons = _evaluate_conditions(
            rule=rule,
            vehicle_count=traffic_record.vehicle_count,
            occupancy_percent=traffic_record.occupancy_percent,
            avg_speed_kph=traffic_record.avg_speed_kph,
            congestion_level=traffic_record.congestion_level,
        )
        if not reasons:
            continue

        source_reference = f'traffic:{traffic_record.id}'
        title = f'Traffic overflow on {traffic_record.camera.code}'
        description = '; '.join(reasons)
        alert, created = _create_alert(
            camera=traffic_record.camera,
            rule=rule,
            source_type=Alert.SourceType.TRAFFIC,
            source_reference=source_reference,
            title=title,
            description=description,
            traffic_record=traffic_record,
        )
        if created:
            created_alerts.append(alert)

    return created_alerts


def evaluate_prediction_alerts(prediction_record):
    ensure_default_alert_rules()
    rules = AlertRule.objects.filter(is_active=True, rule_type=AlertRule.RuleType.PREDICTION).filter(
        Q(camera__isnull=True) | Q(camera=prediction_record.camera)
    )

    created_alerts = []
    for rule in rules:
        if not _rule_applies_to_camera(rule, prediction_record.camera):
            continue

        reasons = _evaluate_conditions(
            rule=rule,
            vehicle_count=prediction_record.predicted_vehicle_count,
            occupancy_percent=prediction_record.predicted_occupancy_percent,
            avg_speed_kph=prediction_record.predicted_avg_speed_kph,
            congestion_level=prediction_record.predicted_congestion_level,
            confidence=prediction_record.confidence,
        )
        if not reasons:
            continue

        source_reference = f'prediction:{prediction_record.id}'
        title = f'Predicted overflow on {prediction_record.camera.code}'
        description = '; '.join(reasons)
        alert, created = _create_alert(
            camera=prediction_record.camera,
            rule=rule,
            source_type=Alert.SourceType.PREDICTION,
            source_reference=source_reference,
            title=title,
            description=description,
            prediction_record=prediction_record,
        )
        if created:
            created_alerts.append(alert)

    return created_alerts


def mark_alert_acknowledged(alert):
    if alert.status == Alert.Status.RESOLVED:
        return alert
    alert.status = Alert.Status.ACKNOWLEDGED
    alert.save(update_fields=['status', 'updated_at'])
    return alert


def mark_alert_resolved(alert):
    alert.status = Alert.Status.RESOLVED
    alert.resolved_at = timezone.now()
    alert.save(update_fields=['status', 'resolved_at', 'updated_at'])
    return alert
