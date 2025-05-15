from django.core.management.base import BaseCommand
from ...retraining.retraining import retraining

class Command(BaseCommand):
    help = 'Executes model training using the formatted data'

    def handle(self, *args, **options):
        result = retraining()
        self.stdout.write(str(result))
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS('Successfully trained model'))
            if result.get('best_model_path'):
                self.stdout.write(self.style.SUCCESS(f'Model saved at: {result.get("best_model_path")}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to train model: {result.get("message", "Unknown error")}'))
