from django.core.management.base import BaseCommand
from ...retraining.retraining_first_reviewer import retraining_first_reviewer_kfold

class Command(BaseCommand):
    help = 'Executes K-fold cross-validation model training for first reviewer data using the formatted data'
    
    def add_arguments(self, parser):
        parser.add_argument('--k', type=int, default=7, help='Number of folds for cross-validation')
        parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
        parser.add_argument('--batch-size', type=int, default=8, help='Training batch size')
        parser.add_argument('--img-size', type=int, default=640, help='Image size for training')
        parser.add_argument('--patience', type=int, default=5, help='Early stopping patience')

    def handle(self, *args, **options):
        k = options.get('k', 7)
        epochs = options.get('epochs', 20)
        batch_size = options.get('batch_size', 8)
        img_size = options.get('img_size', 640)
        patience = options.get('patience', 5)
        
        self.stdout.write(f"Starting first reviewer {k}-fold cross-validation with epochs={epochs}, batch_size={batch_size}, img_size={img_size}")
        
        result = retraining_first_reviewer_kfold(
            k=k, 
            epochs=epochs, 
            batch_size=batch_size,
            img_size=img_size,
            patience=patience
        )
        
        self.stdout.write(str(result))
        
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f"Successfully completed first reviewer {result.get('folds_completed')}/{result.get('total_folds')} folds"))
            
            avg_metrics = result.get('avg_metrics')
            if avg_metrics:
                self.stdout.write(self.style.SUCCESS(f"Average mAP@0.5: {avg_metrics['avg_mAP_0.5']:.4f} ± {avg_metrics['std_mAP_0.5']:.4f}"))
                self.stdout.write(self.style.SUCCESS(f"Average precision: {avg_metrics['avg_precision']:.4f} ± {avg_metrics['std_precision']:.4f}"))
                self.stdout.write(self.style.SUCCESS(f"Average recall: {avg_metrics['avg_recall']:.4f} ± {avg_metrics['std_recall']:.4f}"))
                
            if result.get('best_fold') is not None:
                self.stdout.write(self.style.SUCCESS(f"Best fold: {result.get('best_fold')}"))
                
            self.stdout.write(self.style.SUCCESS(f"Results saved to: {result.get('results_csv')}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to complete first reviewer k-fold training: {result.get('message', 'Unknown error')}"))