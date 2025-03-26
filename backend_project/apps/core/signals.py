from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PreprocessedImage
from .tasks import analyze_image

@receiver(post_save, sender=PreprocessedImage)
def trigger_analysis(sender, instance, created, **kwargs):
    if created:
        analyze_image(instance.id)
