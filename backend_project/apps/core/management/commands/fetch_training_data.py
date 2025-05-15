from django.core.management.base import BaseCommand
from ...retraining.data_collection import fetch_training_data

class Command(BaseCommand):
    help = 'Fetches training data for model retraining'

    def handle(self, *args, **options):
        result = fetch_training_data()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS('Successfully fetched training data'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to fetch training data: {result.get("message", "Unknown error")}'))
