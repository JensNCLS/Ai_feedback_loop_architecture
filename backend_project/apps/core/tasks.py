from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .analysis.analysis import analyze_image
from .models import PreprocessedImage, FeedbackImage, AnalyzedImage
from .retraining.retraining import Model_retrainer
from .feedback.comparing.bbox_comparison import flag_for_review_check
from .logging.logging import get_logger

# Get the logger instance
logger = get_logger()

@shared_task
def analyze_image_task(preprocessed_image_id):
    try:
        analyzed_image = analyze_image(preprocessed_image_id)
        return {"status": "success", "message": "Image analyzed", "analyzed_image_id": analyzed_image.id}
    except Exception as e:
        logger.error(f"Error analyzing image {preprocessed_image_id}: {str(e)}")
        return {"status": "failure", "message": str(e)}

@shared_task
def process_feedback_task(preprocessed_image_id, analyzed_image_id, feedback_data, feedback_text=None):
    try:

        # Get the related objects
        preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
        analyzed_image = AnalyzedImage.objects.get(id=analyzed_image_id)
        
        # Compare AI predictions with feedback and check if it needs review
        needs_review = False
        comparison_result = None
        
        # First, check for the case where AI found nothing but dermatologist did
        ai_predictions = []
        if analyzed_image and analyzed_image.analysis_results:
            ai_predictions = analyzed_image.analysis_results
            
        # Flag for review if AI found nothing but dermatologist did find lesions
        if len(ai_predictions) == 0 and len(feedback_data) > 0:
            needs_review = True
            # Create a basic comparison result for UI display
            comparison_result = {
                'needs_review': True,
                'summary': {
                    'match_count': 0,
                    'missed_detection_count': len(feedback_data),
                    'false_positive_count': 0,
                    'classification_difference_count': 0
                },
                'matches': [],
                'missed_detections': feedback_data,
                'false_positives': []
            }
            logger.warning(f"Image {preprocessed_image_id} flagged for review: AI detected nothing but dermatologist found {len(feedback_data)} lesions")
        # Otherwise run the normal comparison if there are AI predictions
        elif len(ai_predictions) > 0:
            try:
                
                # Run comparison check
                comparison_result = flag_for_review_check(
                    ai_predictions, 
                    feedback_data
                )
                
                needs_review = comparison_result['needs_review']
                
                # Log the comparison results
                logger.info(f"Prediction comparison for image {preprocessed_image_id}: "
                            f"Matches: {comparison_result['summary']['match_count']}, "
                            f"Missed detections: {comparison_result['summary']['missed_detection_count']}, "
                            f"False positives: {comparison_result['summary']['false_positive_count']}, "
                            f"Classification differences: {comparison_result['summary']['classification_difference_count']}")
                
                if needs_review:
                    logger.warning(f"Image {preprocessed_image_id} flagged for review due to significant differences")
            
            except Exception as e:
                logger.error(f"Error during prediction comparison: {str(e)}")
        
        feedback = FeedbackImage.objects.create(
            preprocessed_image=preprocessed_image,
            analyzed_image=analyzed_image,
            feedback_data=feedback_data,
            feedback_text=feedback_text,
            needs_review=needs_review,
            comparison_data=comparison_result
        )
        
        return {
            "status": "success", 
            "feedback_id": feedback.id, 
            "needs_review": needs_review,
            "comparison_summary": comparison_result['summary'] if comparison_result else None
        }
    except Exception as e:
        logger.error(f"Feedback processing error: {str(e)}")
        return {"status": "failure", "message": str(e)}
