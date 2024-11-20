from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from ..models.model_loader import analyze_image


@csrf_exempt  # For simplicity, disable CSRF token checks for now
def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        image_file = request.FILES['image']

        # Pass the image to the model for analysis
        results = analyze_image(image_file)

        # Return the results as JSON
        return JsonResponse({'predictions': results})
    return JsonResponse({'error': 'No image provided'}, status=400)
