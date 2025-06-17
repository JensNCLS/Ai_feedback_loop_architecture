from django.core.management.base import BaseCommand
from ...retraining.data_formatting import format_training_data_kfold

class Command(BaseCommand):
    help = 'Formats training data into K folds for cross-validation'
    
    def add_arguments(self, parser):
        parser.add_argument('--k', type=int, default=7, help='Number of folds for cross-validation')

    def handle(self, *args, **options):
        k = options.get('k', 7)
        self.stdout.write(f"Formatting training data into {k} folds")
        
        result = format_training_data_kfold(k=k)
        self.stdout.write(str(result))
        
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f"Successfully formatted training data into {result.get('folds')} folds"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to format training data: {result.get('message', 'Unknown error')}"))
