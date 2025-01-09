from .models import PreprocessedImage, AnalyzedImage
import requests

def analyze_image(preprocessed_image_id):

    preprocessed_image = PreprocessedImage.objects.get(id=preprocessed_image_id)


    files = {"image": (preprocessed_image.original_filename, preprocessed_image.image, "image/jpeg")}
    url = "http://127.0.0.1:8001/predict/"
    response = requests.post(url, files=files)

    if response.status_code == 200:

        analysis_results = response.json().get("predictions", [])

        analyzed_image = AnalyzedImage.objects.create(
            preprocessed_image=preprocessed_image,
            analysis_results=analysis_results
        )
    else:
        raise Exception(f"Analysis failed: {response.status_code} - {response.text}")
