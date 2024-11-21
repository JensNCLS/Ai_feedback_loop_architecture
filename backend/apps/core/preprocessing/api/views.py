from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
from django.conf import settings
from ....models.model_loader import analyze_image

#python manage.py runserver

@csrf_exempt  # For simplicity, disable CSRF token checks for now
def upload_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']

        # Save the uploaded image to the media directory
        file_path = os.path.join(settings.MEDIA_ROOT, image_file.name)
        path = default_storage.save(file_path, image_file)
        relative_url = os.path.join(settings.MEDIA_URL, image_file.name)  # Relative URL for frontend

        # Pass the image to the model for analysis
        results = analyze_image(image_file)  # Your function to analyze the image

        # Return the results and image URL as JSON
        return JsonResponse({'predictions': results, 'image_url': relative_url})

    return JsonResponse({'error': 'No image provided'}, status=400)
