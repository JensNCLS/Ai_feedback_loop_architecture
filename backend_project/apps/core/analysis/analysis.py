import requests
import io
from ..models import PreprocessedImage, AnalyzedImage
from ..logging.logging import get_logger
from ..utils import get_image_from_minio, upload_image_to_minio

logger = get_logger()

def log_method_call(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with arguments: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            if isinstance(result, dict) and result.get("status") == "failure":
                logger.warning(f"Warning from {func.__name__}: {result.get('message')}")
            logger.info(f"Finished {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

@log_method_call
def analyze_image(preprocessed_image_id):
    preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
    
    image_data = get_image_from_minio(
        preprocessed_image.bucket_name, 
        preprocessed_image.object_name
    )
    
    if not image_data:
        raise Exception(f"Failed to retrieve image from MinIO storage: {preprocessed_image.storage_path}")

    files = {
        "image": (
            preprocessed_image.original_filename, 
            io.BytesIO(image_data), 
            "image/jpeg"
        )
    }

    url = "http://ai_models:8001/predict/"
    response = requests.post(url, files=files)

    if response.status_code == 200:
        analysis_results = response.json().get("predictions", [])
        
        analyzed_image = AnalyzedImage.objects.create(
            preprocessed_image=preprocessed_image,
            analysis_results=analysis_results,
        )
        
        if "result_image" in response.json():
            result_image = response.json().get("result_image")
            if result_image:
                result_bucket, result_object = upload_image_to_minio(
                    result_image, 
                    f"result_{preprocessed_image.original_filename}"
                )
                
                analyzed_image.result_bucket_name = result_bucket
                analyzed_image.result_object_name = result_object
                analyzed_image.save()

        return analyzed_image
    else:
        raise Exception(f"Analysis failed: {response.status_code} - {response.text}")
