from celery import shared_task

@shared_task
def analyze_image(image_id):
    # Code to process the image (e.g., run your AI model)
    # This is a placeholder, replace it with actual logic
    print(f"Analyzing image {image_id}")
    return f"Analysis of image {image_id} complete"
