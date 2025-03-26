from django.db import models

class PreprocessedImage(models.Model):
    image = models.BinaryField()

    original_filename = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Preprocessed Image {self.id} - {self.original_filename}"

class AnalyzedImage(models.Model):
    preprocessed_image = models.OneToOneField(
        PreprocessedImage,
        on_delete=models.CASCADE,
        related_name="analyzed_image"
    )
    analysis_results = models.JSONField(null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for Image {self.preprocessed_image.id}"

class FeedbackImage(models.Model):
    preprocessed_image = models.ForeignKey(
        'PreprocessedImage',
        on_delete=models.CASCADE,
        related_name='feedback_images'
    )
    analyzed_image = models.ForeignKey(
        'AnalyzedImage',
        on_delete=models.CASCADE,
        related_name='feedback_images',
        null=True, blank=True
    )
    feedback_data = models.JSONField()
    feedback_text = models.TextField(blank=True, null=True)
    feedback_given_at = models.DateTimeField(auto_now_add=True)
    retrained = models.BooleanField(default=False)

    def __str__(self):
        return f"Feedback for Image {self.preprocessed_image.id}"

class LogEntry(models.Model):
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    module = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.level}: {self.message}"

