from django.core.management.base import BaseCommand
from ...retraining.retraining_first_reviewer import retraining_first_reviewer

class Command(BaseCommand):
    help = 'Executes model training using the first reviewer formatted data'

    def handle(self, *args, **options):
        result = retraining_first_reviewer()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS('Successfully trained first reviewer model'))
            if result.get('best_model_path'):
                self.stdout.write(self.style.SUCCESS(f'Model saved at: {result.get("best_model_path")}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to train model: {result.get("message", "Unknown error")}'))
