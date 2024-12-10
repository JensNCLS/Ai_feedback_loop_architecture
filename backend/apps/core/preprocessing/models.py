from django.db import models

class PreprocessedImage(models.Model):
    image = models.BinaryField()

    original_filename = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Preprocessed Image {self.id} - {self.original_filename}"
