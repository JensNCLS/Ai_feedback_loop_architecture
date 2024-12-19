from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ...analysis.models import AnalyzedImage
from ..models import PreprocessedImage
import requests
import logging


@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and 'image' in request.FILES:
        try:
            image_file = request.FILES['image']

            preprocessed_image = PreprocessedImage.objects.create(
                image=image_file.read(),
                original_filename=image_file.name
            )

            image_file.seek(0)

            files = {
                "image": ("image.jpg", image_file, "image/jpeg")
            }

            url = "http://127.0.0.1:8001/predict/"
            response = requests.post(url, files=files)
            response.raise_for_status()

            analysis_results = response.json().get("predictions", [])

            analyzed_image = AnalyzedImage.objects.create(
                preprocessed_image=preprocessed_image,
                analysis_results=analysis_results
            )

            return JsonResponse({
                "success": True,
                "message": "Image successfully uploaded and analysis completed!",
                "image_id": preprocessed_image.id,
                "analysis_results": analysis_results,
                "analyzed_image_id": analyzed_image.id
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No image provided"}, status=400)



