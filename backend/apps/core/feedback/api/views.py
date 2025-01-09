from django.http import JsonResponse
from ...models import AnalyzedImage, PreprocessedImage
from django.shortcuts import get_object_or_404

def check_analysis_status(request, preprocessed_image_id):
    try:

        preprocessed_image = get_object_or_404(PreprocessedImage, id=preprocessed_image_id)

        analyzed_image = AnalyzedImage.objects.filter(preprocessed_image=preprocessed_image).first()

        if analyzed_image:
            return JsonResponse({
                "success": True,
                "status": "completed",
                "analysis_results": analyzed_image.analysis_results
            })
        else:
            return JsonResponse({
                "success": True,
                "status": "in_progress"
            })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
