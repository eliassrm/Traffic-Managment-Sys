from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from traffic.models import Traffic, TrafficPrediction

from alerts.services import evaluate_prediction_alerts, evaluate_traffic_alerts, ensure_default_alert_rules


class Command(BaseCommand):
    help = 'Evaluate recent traffic and prediction records against alert rules.'

    def add_arguments(self, parser):
        parser.add_argument('--lookback-minutes', type=int, default=30)

    def handle(self, *args, **options):
        lookback_minutes = options['lookback_minutes']
        cutoff = timezone.now() - timedelta(minutes=lookback_minutes)

        ensure_default_alert_rules()

        traffic_records = Traffic.objects.filter(measured_at__gte=cutoff)
        prediction_records = TrafficPrediction.objects.filter(predicted_for__gte=cutoff)

        created_alerts = 0
        for record in traffic_records:
            created_alerts += len(evaluate_traffic_alerts(record))

        for prediction in prediction_records:
            created_alerts += len(evaluate_prediction_alerts(prediction))

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed alerts with lookback={lookback_minutes}m. Created {created_alerts} alert(s).'
            )
        )
