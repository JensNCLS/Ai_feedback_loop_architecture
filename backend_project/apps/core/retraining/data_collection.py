from ..logging.logging import get_logger
from ..models import FeedbackImage
from pathlib import Path
import json

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
def fetch_training_data():
    try:
        feedback_images = FeedbackImage.objects.filter(status='reviewed', retrained=False)
        
        if not feedback_images.exists():
            logger.info("No feedback images to process.")
            return {"status": "success", "message": "No feedback images to process."}
        
        base_dir = Path(__file__).parent.parent.parent.parent / "media"
        images_train_dir = base_dir / "raw" 
        images_train_dir.mkdir(parents=True, exist_ok=True)
        
        data = []
        for img in feedback_images:
            row = {
                'id': img.id,
                'preprocessed_image_id': img.preprocessed_image_id,
                'bucket_name': img.preprocessed_image.bucket_name,
                'object_name': img.preprocessed_image.object_name,
                'original_filename': img.preprocessed_image.original_filename,
                'feedback_data': img.feedback_data,
                'status': img.status,
                'retrained': img.retrained
            }
            data.append(row)
        
        # Convert Django model objects to JSON-serializable format
        def json_serializer(obj):
            try:
                return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
            except:
                return str(obj)
        
        with open(images_train_dir / "feedback_images.json", 'w') as f:
            json.dump(data, f, indent=2, default=json_serializer)
        
        return {"status": "success", "message": f"Exported {len(data)} feedback images to JSON", "count": len(data)}
        
    except Exception as e:
        logger.error(f"Error in fetch_and_format_training_data: {e}")
        return {"status": "failure", "message": str(e), "count": 0}