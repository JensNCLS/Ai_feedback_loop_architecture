from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .analysis.analysis import analyze_image
from .models import PreprocessedImage, FeedbackImage, AnalyzedImage, LogEntry
from .retraining.retraining import Model_retrainer
from .feedback.comparing.bbox_comparison import flag_for_review_check

@shared_task
def analyze_image_task(preprocessed_image_id):
    try:
        analyzed_image = analyze_image(preprocessed_image_id)
        return {"status": "success", "message": "Image analyzed", "analyzed_image_id": analyzed_image.id}
    except Exception as e:
        return {"status": "failure", "message": str(e)}

@shared_task
def preprocess_image_task(preprocessed_image_id):
    try:
        # Get the preprocessed image
        preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
        
        # Trigger analysis as the next step in the pipeline
        analyze_image_task.delay(preprocessed_image.id)
        
        return {"status": "success", "preprocessed_image_id": preprocessed_image.id}
    except Exception as e:
        log_event_task.delay('ERROR', f"Preprocessing error: {str(e)}", 'preprocessing')
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
            log_event_task.delay('WARNING', f"Image {preprocessed_image_id} flagged for review: AI detected nothing but dermatologist found {len(feedback_data)} lesions", 'feedback')
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
                log_event_task.delay('INFO', f"Prediction comparison for image {preprocessed_image_id}: "
                            f"Matches: {comparison_result['summary']['match_count']}, "
                            f"Missed detections: {comparison_result['summary']['missed_detection_count']}, "
                            f"False positives: {comparison_result['summary']['false_positive_count']}, "
                            f"Classification differences: {comparison_result['summary']['classification_difference_count']}", 'feedback')
                
                if needs_review:
                    log_event_task.delay('WARNING', f"Image {preprocessed_image_id} flagged for review due to significant differences", 'feedback')
            
            except Exception as e:
                log_event_task.delay('ERROR', f"Error during prediction comparison: {str(e)}", 'feedback')
        
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
        log_event_task.delay('ERROR', f"Feedback processing error: {str(e)}", 'feedback')
        return {"status": "failure", "message": str(e)}

@shared_task
def retrain_model_task(feedback_ids=None):
    try:
        log_event_task.delay('INFO', "Starting model retraining process", 'retraining')
        
        # Initialize the retrainer
        retrainer = Model_retrainer()
        
        # If specific feedback IDs are provided, use only those
        if feedback_ids:
            feedbacks = FeedbackImage.objects.filter(id__in=feedback_ids)
            # Custom logic would be needed here to use only specific feedbacks
            # For now, we'll just use the standard retraining process
        
        # Use the existing retraining logic
        result = retrainer.retrain_model()
        
        if result['status'] == 'success':
            log_event_task.delay('INFO', f"Model retrained successfully: {result['message']}", 'retraining')
        else:
            log_event_task.delay('WARNING', f"Retraining issue: {result['message']}", 'retraining')
        
        return result
    except Exception as e:
        error_message = f"Retraining error: {str(e)}"
        log_event_task.delay('ERROR', error_message, 'retraining')
        return {"status": "failure", "message": error_message}

@shared_task
def log_event_task(level, message, module=None):
    try:
        LogEntry.objects.create(
            level=level,
            message=message,
            module=module
        )
        return {"status": "success"}
    except Exception as e:
        # In case of logging failure, print to console as last resort
        print(f"Logging error: {e}")
        print(f"Original log: [{level}] {module}: {message}")
        return {"status": "failure", "message": str(e)}
