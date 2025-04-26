from django.db import models

class PreprocessedImage(models.Model):
    original_filename = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # MinIO storage fields
    bucket_name = models.CharField(max_length=100, default='skinimages')
    object_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Preprocessed Image {self.id} - {self.original_filename}"
        
    @property
    def storage_path(self):
        """Return the full storage path in the format 'bucket_name/object_name'"""
        if self.bucket_name and self.object_name:
            return f"{self.bucket_name}/{self.object_name}"
        return None

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
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
    ]
    
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
    needs_review = models.BooleanField(default=False)
    comparison_data = models.JSONField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)

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

