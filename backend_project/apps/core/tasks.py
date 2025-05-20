from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .analysis.analysis import analyze_image
from .models import PreprocessedImage, FeedbackImage, AnalyzedImage, FirstReviewerFeedbackImage
from .feedback.comparing.bbox_comparison import flag_for_review_check
from .logging.logging import get_logger
from .retraining.retraining import retraining

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
def process_unreviewed_feedback_task(preprocessed_image_id, analyzed_image_id, feedback_data, feedback_text=None):
    try:
        preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
        analyzed_image = AnalyzedImage.objects.get(id=analyzed_image_id)
        
        feedback = FirstReviewerFeedbackImage.objects.create(
            preprocessed_image=preprocessed_image,
            analyzed_image=analyzed_image,
            feedback_data=feedback_data,
            feedback_text=feedback_text,
        )
        
        return {
            "status": "success", 
            "feedback_id": feedback.id
        }
        
    except Exception as e:
        logger.error(f"Error in process_unreviewed_feedback_task: {e}")
        return {"status": "failure", "message": str(e)}

@shared_task
def process_feedback_task(preprocessed_image_id, analyzed_image_id, feedback_data, feedback_text=None):
    try:
        preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
        analyzed_image = AnalyzedImage.objects.get(id=analyzed_image_id)
        
        needs_review = False
        comparison_result = None
        status = 'reviewed'
        
        ai_predictions = []
        if analyzed_image and analyzed_image.analysis_results:
            ai_predictions = analyzed_image.analysis_results
            
        if len(ai_predictions) == 0 and len(feedback_data) > 0:
            needs_review = True
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
            status = "pending"

        elif len(ai_predictions) > 0:
            try:
                comparison_result = flag_for_review_check(
                    ai_predictions, 
                    feedback_data
                )
                
                needs_review = comparison_result['needs_review']
                
                logger.info(f"Prediction comparison for image {preprocessed_image_id}: "
                            f"Matches: {comparison_result['summary']['match_count']}, "
                            f"Missed detections: {comparison_result['summary']['missed_detection_count']}, "
                            f"False positives: {comparison_result['summary']['false_positive_count']}, "
                            f"Classification differences: {comparison_result['summary']['classification_difference_count']}")
                
                if needs_review:
                    logger.warning(f"Image {preprocessed_image_id} flagged for review due to significant differences")
                    status = "pending"
            
            except Exception as e:
                logger.error(f"Error during prediction comparison: {str(e)}")
        
        feedback = FeedbackImage.objects.create(
            preprocessed_image=preprocessed_image,
            analyzed_image=analyzed_image,
            feedback_data=feedback_data,
            feedback_text=feedback_text,
            needs_review=needs_review,
            comparison_data=comparison_result,
            status=status
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