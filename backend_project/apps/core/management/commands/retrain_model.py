from django.core.management.base import BaseCommand
from apps.core.retraining.retraining import retrain_model
import time

class Command(BaseCommand):
    help = 'Retrain the YOLOv5 model using feedback data'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=5,
                            help='Number of training epochs')
        parser.add_argument('--img_size', type=int, default=1280,
                            help='Input image size for training')
        parser.add_argument('--batch_size', type=int, default=8,
                            help='Batch size for training')
        parser.add_argument('--weights', type=str, default=None,
                            help='Pre-trained weights to use (default: yolov5s.pt)')

    def handle(self, *args, **options):
        self.stdout.write("Starting model retraining...")
        start_time = time.time()
        
        result = retrain_model(
            epochs=options['epochs'],
            img_size=options['img_size'],
            batch_size=options['batch_size'],
            weights=options['weights']
        )
        
        duration = time.time() - start_time
        
        if result['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(f"✅ Retraining successful! (took {duration:.2f} seconds)"))
            self.stdout.write(f"MLFlow URL: {result.get('mlflow_url')}")
            self.stdout.write(f"New model path: {result.get('training_result', {}).get('best_weights')}")
        elif result['status'] == 'skipped':
            self.stdout.write(self.style.WARNING(f"⚠️ Retraining skipped: {result.get('message')}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Retraining failed: {result.get('message')}"))