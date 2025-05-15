from django.core.management.base import BaseCommand
from ...retraining.data_formatting import format_training_data

class Command(BaseCommand):
    help = 'Formats training data for model retraining'

    def handle(self, *args, **options):
        result = format_training_data()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS('Successfully formatted training data'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to format training data: {result.get("message", "Unknown error")}'))
