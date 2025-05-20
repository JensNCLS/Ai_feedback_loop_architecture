from django.core.management.base import BaseCommand
from ...retraining.data_collection_first_reviewer import fetch_first_reviewer_training_data

class Command(BaseCommand):
    help = 'Fetches training data from FirstReviewerFeedbackImage model'

    def handle(self, *args, **options):
        result = fetch_first_reviewer_training_data()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f'Successfully collected {result.get("count", 0)} feedback items'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to collect data: {result.get("message", "Unknown error")}'))
