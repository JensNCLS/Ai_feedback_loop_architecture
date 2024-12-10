import torch
from PIL import Image
from pathlib import Path

model_path = Path("best.pt")
model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=True)

# Function to analyze a single image passed as a file path
def analyze_image(image_path):
    # Open the image using PIL directly from the file path
    image = Image.open(image_path)

    # Run inference on the image using YOLOv5
    results = model(image)

    # Extract predictions as a DataFrame
    predictions = results.pandas().xyxy[0]  # Extract predictions in xyxy format

    # Return predictions as a dictionary or JSON object
    return predictions.to_dict(orient="records")
