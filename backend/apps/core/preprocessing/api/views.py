from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import PreprocessedImage
from django.shortcuts import render
from ...analysis.tasks import analyze_image

@csrf_exempt  # For simplicity, disable CSRF token checks for now
def upload_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']

        # Convert uploaded image file to binary format
        image_binary = image_file.read()

        # Save the image to the database
        preprocessed_image = PreprocessedImage.objects.create(image=image_binary)

        analyze_image.delay(preprocessed_image.id)

        # Return the results and image ID as JSON (or you can return the URL if you want)
        return JsonResponse({
            'success': True,
            'message': 'Image successfully uploaded and analysis started!',
            'image_id': preprocessed_image.id
        })

    return JsonResponse({'error': 'No image provided'}, status=400)