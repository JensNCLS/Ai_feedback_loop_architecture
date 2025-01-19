import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...models import AnalyzedImage, PreprocessedImage, FeedbackImage
from django.shortcuts import get_object_or_404
from ...logging.logging import get_logger

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

            try:
                preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
            except PreprocessedImage.DoesNotExist:
                return JsonResponse({'error': 'Preprocessed image not found.'}, status=404)

            analyzed_image = None
            if analyzed_image_id:
                try:
                    analyzed_image = AnalyzedImage.objects.get(id=analyzed_image_id)
                except AnalyzedImage.DoesNotExist:
                    return JsonResponse({'error': 'Analyzed image not found.'}, status=404)

            feedback = FeedbackImage(
                preprocessed_image=preprocessed_image,
                analyzed_image=analyzed_image,
                feedback_data=predictions,
                feedback_text=feedback_text
            )
            feedback.save()

            return JsonResponse({'message': 'Feedback successfully submitted!'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)
