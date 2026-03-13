from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from traffic.models import Traffic, TrafficArchive


class Command(BaseCommand):
    help = 'Archive old traffic records into TrafficArchive table.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-days', type=int, default=30)
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        older_than_days = options['older_than_days']
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        cutoff = timezone.now() - timedelta(days=older_than_days)
        queryset = Traffic.objects.filter(measured_at__lt=cutoff).order_by('id')
        total_candidates = queryset.count()

        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS('No traffic records eligible for archival.'))
            return

        self.stdout.write(
            self.style.WARNING(
                f'Found {total_candidates} traffic record(s) older than {older_than_days} days.'
            )
        )

        archived_total = 0
        for start in range(0, total_candidates, batch_size):
            batch = list(queryset[start:start + batch_size])
            archive_rows = [
                TrafficArchive(
                    source_record_id=item.id,
                    camera=item.camera,
                    measured_at=item.measured_at,
                    vehicle_count=item.vehicle_count,
                    avg_speed_kph=item.avg_speed_kph,
                    congestion_level=item.congestion_level,
                    occupancy_percent=item.occupancy_percent,
                    original_created_at=item.created_at,
                    original_updated_at=item.updated_at,
                )
                for item in batch
            ]

            if dry_run:
                archived_total += len(archive_rows)
                continue

            with transaction.atomic():
                TrafficArchive.objects.bulk_create(archive_rows, ignore_conflicts=True)
                batch_ids = [item.id for item in batch]
                inserted_ids = set(
                    TrafficArchive.objects.filter(source_record_id__in=batch_ids).values_list(
                        'source_record_id', flat=True
                    )
                )
                if inserted_ids:
                    Traffic.objects.filter(id__in=inserted_ids).delete()
                    archived_total += len(inserted_ids)

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Dry run: would archive {archived_total} record(s).'))
            return

        self.stdout.write(self.style.SUCCESS(f'Archived {archived_total} record(s) successfully.'))
