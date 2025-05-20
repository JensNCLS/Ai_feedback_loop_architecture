from django.core.management.base import BaseCommand
from ...retraining.data_formatting_first_reviewer import format_first_reviewer_training_data

class Command(BaseCommand):
    help = 'Format training data collected from FirstReviewerFeedbackImage model'

    def handle(self, *args, **options):
        result = format_first_reviewer_training_data()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f'Successfully formatted {result.get("count", 0)} training images'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to format data: {result.get("message", "Unknown error")}'))
