from celery import shared_task
from .analysis.analysis import analyze_image

@shared_task
def analyze_image_task(preprocessed_image_id):
    try:
        analyzed_image = analyze_image(preprocessed_image_id)
        return {"status": "success", "message": "Image analyzed", "analyzed_image_id": analyzed_image.id}
    except Exception as e:
        return {"status": "failure", "message": str(e)}
