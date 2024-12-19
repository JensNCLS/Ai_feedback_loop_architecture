from django.db import models
from ..preprocessing.models import PreprocessedImage

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
