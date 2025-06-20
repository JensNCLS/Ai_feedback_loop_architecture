from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...models import PreprocessedImage
from ...tasks import analyze_image_task
from ...logging.logging import get_logger
from ...utils import upload_image_to_minio

logger = get_logger()

#startup commands:
#Django: python manage.py runserver
#FastApi: uvicorn apps.ai_models.app:app --port 8001
#React: npm start
#retrain: python manage.py retrain_model

def log_method_call(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with arguments: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Finished {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

@csrf_exempt
@log_method_call
def upload_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        try:
            image_file = request.FILES['image']
            image_data = image_file.read()
            
            bucket_name, object_name = upload_image_to_minio(image_data, image_file.name)
            
            preprocessed_image = PreprocessedImage.objects.create(
                original_filename=image_file.name,
                bucket_name=bucket_name,
                object_name=object_name
            )

            analyze_image_task.delay(preprocessed_image.id)
            
            return JsonResponse({
                "success": True,
                "message": "Image successfully uploaded and analysis started!",
                "preprocessed_image_id": preprocessed_image.id
            })

        except Exception as e:
            logger.error(f"Image upload error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No image provided"}, status=400)



