from django.core.management.base import BaseCommand
from ...retraining.data_formatting_first_reviewer import format_first_reviewer_training_data_kfold

class Command(BaseCommand):
    help = 'Formats first reviewer training data into K folds for cross-validation'
    
    def add_arguments(self, parser):
        parser.add_argument('--k', type=int, default=7, help='Number of folds for cross-validation')

    def handle(self, *args, **options):
        k = options.get('k', 7)
        self.stdout.write(f"Formatting first reviewer training data into {k} folds")
        
        result = format_first_reviewer_training_data_kfold(k=k)
        self.stdout.write(str(result))
        
        if result.get('status') == 'success':
            self.stdout.write(self.style.SUCCESS(f"Successfully formatted first reviewer training data into {result.get('folds')} folds"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to format first reviewer training data: {result.get('message', 'Unknown error')}"))