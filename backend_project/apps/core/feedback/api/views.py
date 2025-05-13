import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from ...models import AnalyzedImage, PreprocessedImage, FeedbackImage
from django.shortcuts import get_object_or_404
from ...logging.logging import get_logger
from ...tasks import process_feedback_task
from django.core.paginator import Paginator

logger = get_logger()

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

@log_method_call
def get_review_items(request):
    try:
        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 8))
        status = request.GET.get('status', None)
        sort_by = request.GET.get('sort_by', 'newest')
        
        queryset = FeedbackImage.objects.filter(needs_review=True)
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        if sort_by == 'oldest':
            queryset = queryset.order_by('feedback_given_at')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-feedback_given_at')
            
        feedback_items = queryset.select_related('preprocessed_image', 'analyzed_image')
        
        paginator = Paginator(feedback_items, page_size)
        current_page = paginator.get_page(page_number)
        
        items = []
        for feedback in current_page:
            
            image_url = None
            if feedback.preprocessed_image:
                # Simply create an API URL to fetch the image
                image_url = f"/api/image/{feedback.preprocessed_image.id}/"
            
            prediction_count = len(feedback.feedback_data) if feedback.feedback_data else 0
            
            review_reason = "Manual review needed"
            if feedback.comparison_data and 'summary' in feedback.comparison_data:
                summary = feedback.comparison_data['summary']
                if summary.get('missed_detection_count', 0) > 0:
                    review_reason = f"Missed detections: {summary['missed_detection_count']}"
                elif summary.get('false_positive_count', 0) > 0:
                    review_reason = f"False positives: {summary['false_positive_count']}"
                elif summary.get('classification_difference_count', 0) > 0:
                    review_reason = f"Classification differences: {summary['classification_difference_count']}"
            
            items.append({
                'id': feedback.id,
                'image_url': image_url,
                'feedback_given_at': feedback.feedback_given_at.isoformat(),
                'status': feedback.status,
                'review_reason': review_reason,
                'prediction_count': prediction_count,
                'preprocessed_image_id': feedback.preprocessed_image.id,
                'analyzed_image_id': feedback.analyzed_image.id if feedback.analyzed_image else None
            })
        
        return JsonResponse({
            'items': items,
            'total_pages': paginator.num_pages,
            'current_page': page_number,
            'total_items': paginator.count
        })
    except Exception as e:
        logger.error(f"Error fetching review items: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@log_method_call
def get_review_detail(request, feedback_id):
    try:
        feedback = get_object_or_404(FeedbackImage, id=feedback_id)
        
        # Create a data URL for the image from MinIO storage
        image_url = None
        if feedback.preprocessed_image:
            try:
                from ...utils import get_image_from_minio
                import base64
                
                # Retrieve image data from MinIO
                image_data = get_image_from_minio(
                    feedback.preprocessed_image.bucket_name,
                    feedback.preprocessed_image.object_name
                )
                
                if image_data:
                    # Convert binary data to base64 for data URL
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    # Assuming JPEG format, adjust if needed
                    image_url = f"data:image/jpeg;base64,{image_base64}"
                else:
                    # Fall back to API URL if MinIO retrieval fails
                    image_url = f"/api/image/{feedback.preprocessed_image.id}/"
            except Exception as e:
                logger.error(f"Error retrieving image from MinIO: {e}")
                # Fall back to API URL
                image_url = f"/api/image/{feedback.preprocessed_image.id}/"
        
        # Get original AI predictions and feedback predictions
        ai_predictions = feedback.analyzed_image.analysis_results if feedback.analyzed_image else []
        feedback_predictions = feedback.feedback_data if feedback.feedback_data else []
        
        # Add detailed logging to help diagnose the issue
        logger.info(f"Review detail for feedback ID {feedback_id}:")
        logger.info(f"Feedback data type: {type(feedback.feedback_data)}")
        logger.info(f"Feedback data content: {feedback.feedback_data}")
        logger.info(f"Predictions count: {len(feedback_predictions)}")
        
        # Get comparison data if available
        comparison_data = feedback.comparison_data if feedback.comparison_data else {}
        
        return JsonResponse({
            'id': feedback.id,
            'image_url': image_url,
            'feedback_given_at': feedback.feedback_given_at.isoformat(),
            'feedback_text': feedback.feedback_text,
            'status': feedback.status,
            'review_notes': feedback.review_notes if feedback.review_notes else '',
            'predictions': feedback_predictions,  # Use feedback predictions as the starting point for review
            'ai_predictions': ai_predictions,
            'comparison_data': comparison_data,
            'preprocessed_image_id': feedback.preprocessed_image.id,
            'analyzed_image_id': feedback.analyzed_image.id if feedback.analyzed_image else None
        })
    except Exception as e:
        logger.error(f"Error fetching review detail: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@log_method_call
def check_analysis_status(request, preprocessed_image_id):
    try:
        preprocessed_image = get_object_or_404(PreprocessedImage, id=preprocessed_image_id)

        analyzed_image = AnalyzedImage.objects.filter(preprocessed_image=preprocessed_image).first()

        if analyzed_image:
            return JsonResponse({
                "success": True,
                "status": "completed",
                "analysis_results": analyzed_image.analysis_results,
                "analyzed_image_id": analyzed_image.id
            })
        else:
            return JsonResponse({
                "success": True,
                "status": "in_progress"
            })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@log_method_call
def submit_feedback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            preprocessed_image_id = data.get('preprocessed_image_id')
            predictions = data.get('predictions')
            feedback_text = data.get('feedback', '')
            analyzed_image_id = data.get('analyzed_image_id')

            if not preprocessed_image_id or not predictions:
                return JsonResponse({'error': 'Missing preprocessed image ID or predictions.'}, status=400)

            if not PreprocessedImage.objects.filter(id=preprocessed_image_id).exists():
                return JsonResponse({'error': 'Preprocessed image not found.'}, status=404)

            if analyzed_image_id and not AnalyzedImage.objects.filter(id=analyzed_image_id).exists():
                return JsonResponse({'error': 'Analyzed image not found.'}, status=404)
            
            task = process_feedback_task.delay(
                preprocessed_image_id=preprocessed_image_id,
                analyzed_image_id=analyzed_image_id,
                feedback_data=predictions,
                feedback_text=feedback_text
            )

            return JsonResponse({
                'message': 'Feedback successfully submitted!',
                'task_id': task.id
            }, status=202)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)

@csrf_exempt
@log_method_call
def submit_review(request, feedback_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        predictions = data.get('predictions', [])
        review_notes = data.get('review_notes', '')
        status = data.get('status', 'reviewed')
        
        feedback = get_object_or_404(FeedbackImage, id=feedback_id)
        
        feedback.feedback_data = predictions
        feedback.review_notes = review_notes
        feedback.status = status
        feedback.reviewed_at = timezone.now()
        
        feedback.save()
        
        return JsonResponse({'message': 'Review submitted successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@log_method_call
def get_image(request, image_id):
    try:
        preprocessed_image = get_object_or_404(PreprocessedImage, id=image_id)
        
        try:
            from ...utils import get_image_from_minio
            
            # Get image data from MinIO storage
            image_data = get_image_from_minio(
                preprocessed_image.bucket_name,
                preprocessed_image.object_name
            )
            
            if image_data:
                # Return the image directly as binary data with appropriate content type
                return HttpResponse(
                    image_data,
                    content_type='image/jpeg'  # Adjust if you have other image types
                )
            else:
                logger.error(f"Image data not found in MinIO for image {image_id}")
                return HttpResponse(status=404)
        except Exception as e:
            logger.error(f"Error retrieving image from MinIO: {e}")
            return HttpResponse(status=500)
    except Exception as e:
        logger.error(f"Error serving image {image_id}: {e}")
        return HttpResponse(status=500)
