from django.core.management.base import BaseCommand
from ...tasks import retrain_model_task
from datetime import datetime

class Command(BaseCommand):
    help = 'Collects feedback and retrains the AI model using Celery task'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting model retraining (async) at {}'.format(datetime.now()))
        
        # Run the task asynchronously
        task = retrain_model_task.delay()
        
        self.stdout.write(self.style.SUCCESS(f'Retraining task initiated with task ID: {task.id}'))
        self.stdout.write(self.style.WARNING('Check celery logs for progress and results.'))
