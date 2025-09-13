from django.core.management.base import BaseCommand
from api.tasks import ingest_data


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run ingestion synchronously (default is async via Celery)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                'Note: Ensure Excel files are placed in /app/data/ directory:\n'
                '  - customer_data.xlsx\n'
                '  - loan_data.xlsx'
            )
        )
        
        if options['sync']:
            # Run synchronously
            self.stdout.write('Starting synchronous data ingestion...')
            try:
                result = ingest_data()
                self.stdout.write(self.style.SUCCESS(result))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Data ingestion failed: {e}')
                )
        else:
            # Run via Celery worker (default)
            self.stdout.write('Queuing data ingestion task...')
            result = ingest_data.delay()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully queued ingestion task with ID: {result.id}\n'
                    f'Check worker logs for progress.'
                )
            )
