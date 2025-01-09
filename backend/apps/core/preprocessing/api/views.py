from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...models import PreprocessedImage
from ...tasks import analyze_image

#startup commands:
#Django: python manage.py runserver
#FastApi: uvicorn apps.ai_models.app:app --port 8001
#React: npm start

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        try:
            image_file = request.FILES['image']

            # Save the image to PreprocessedImage model as bytes
            preprocessed_image = PreprocessedImage.objects.create(
                image=image_file.read(),  # Save file as binary data
                original_filename=image_file.name
            )

            # Trigger analysis task
            analyze_image(preprocessed_image.id)

            return JsonResponse({
                "success": True,
                "message": "Image successfully uploaded and analysis started!",
                "preprocessed_image_id": preprocessed_image.id
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No image provided"}, status=400)



