from django.core.management.base import BaseCommand
from ...retraining import retraining
from datetime import datetime

class Command(BaseCommand):
    help = 'Collects feedback and retrains the AI model'

    def handle(self, *args, **kwargs):
        retrainer = retraining.Model_retrainer()

        retrained_model_info = retrainer.retrain_model()

        if retrained_model_info['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(f'Model retrained successfully at {datetime.now()}'))
        else:
            self.stdout.write(self.style.ERROR(f'Retraining failed: {retrained_model_info["message"]}'))
