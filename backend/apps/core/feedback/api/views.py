import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...models import AnalyzedImage, PreprocessedImage, FeedbackImage
from django.shortcuts import get_object_or_404

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
def submit_feedback(request):
    if request.method == 'POST':
        try:
            # Parse the incoming data from the frontend
            data = json.loads(request.body.decode('utf-8'))
            preprocessed_image_id = data.get('preprocessed_image_id')
            predictions = data.get('predictions')  # Predictions should contain bounding boxes
            feedback_text = data.get('feedback', '')  # Optional feedback text
            analyzed_image_id = data.get('analyzed_image_id')  # Get the analyzed image ID

            # Check if the required data is present
            if not preprocessed_image_id or not predictions:
                return JsonResponse({'error': 'Missing preprocessed image ID or predictions.'}, status=400)

            # Retrieve the PreprocessedImage instance
            try:
                preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)
            except PreprocessedImage.DoesNotExist:
                return JsonResponse({'error': 'Preprocessed image not found.'}, status=404)

            # Optionally retrieve the AnalyzedImage if provided
            analyzed_image = None
            if analyzed_image_id:
                try:
                    analyzed_image = AnalyzedImage.objects.get(id=analyzed_image_id)
                except AnalyzedImage.DoesNotExist:
                    return JsonResponse({'error': 'Analyzed image not found.'}, status=404)

            # Create a new FeedbackImage instance (analyzed image is optional)
            feedback = FeedbackImage(
                preprocessed_image=preprocessed_image,
                analyzed_image=analyzed_image,
                feedback_data=predictions,  # Store bounding boxes and predictions
                feedback_text=feedback_text  # Store optional feedback text
            )
            feedback.save()

            # Return a success response
            return JsonResponse({'message': 'Feedback successfully submitted!'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)

