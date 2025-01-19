import requests
from ..models import PreprocessedImage, AnalyzedImage
from ..logging.logging import get_logger

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

    files = {"image": (preprocessed_image.original_filename, preprocessed_image.image, "image/jpeg")}

    url = "http://127.0.0.1:8001/predict/"
    response = requests.post(url, files=files)

    if response.status_code == 200:
        analysis_results = response.json().get("predictions", [])

        AnalyzedImage.objects.create(
            preprocessed_image=preprocessed_image,
            analysis_results=analysis_results
        )

        return {"status": "success", "message": "Analysis completed successfully."}
    else:
        raise Exception(f"Analysis failed: {response.status_code} - {response.text}")
