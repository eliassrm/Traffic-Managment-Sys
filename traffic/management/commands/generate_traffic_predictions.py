import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from traffic.prediction_service import generate_predictions_for_all_cameras


class Command(BaseCommand):
    help = 'Generate traffic predictions with Markov chain + Kalman filtering.'

    def add_arguments(self, parser):
        parser.add_argument('--horizon-minutes', type=int, default=5)
        parser.add_argument('--min-samples', type=int, default=5)
        parser.add_argument('--loop', action='store_true')
        parser.add_argument('--interval-seconds', type=int, default=300)

    def handle(self, *args, **options):
        if options['loop']:
            self.stdout.write(self.style.WARNING('Starting continuous prediction loop. Press Ctrl+C to stop.'))
            try:
                while True:
                    self._run_once(options)
                    time.sleep(options['interval_seconds'])
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Prediction loop stopped.'))
            return

        self._run_once(options)

    def _run_once(self, options):
        predictions = generate_predictions_for_all_cameras(
            horizon_minutes=options['horizon_minutes'],
            min_samples=options['min_samples'],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{timezone.now().isoformat()} - generated {len(predictions)} traffic prediction(s)."
            )
        )
