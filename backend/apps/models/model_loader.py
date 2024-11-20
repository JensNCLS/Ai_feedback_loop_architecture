import torch
from pathlib import Path
from io import BytesIO
from PIL import Image
import numpy as np

# Load your custom YOLOv5 model
model_path = 'apps/models/best.pt'
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)


# Function to analyze a single image passed as an image file object
def analyze_image(image_file):
    # Convert the uploaded image to a PIL Image
    image = Image.open(BytesIO(image_file.read()))

    # Run inference on the image using YOLOv5
    results = model(image)

    # Extract predictions as a DataFrame
    predictions = results.pandas().xyxy[0]  # Extract predictions in xyxy format

    # Return predictions as a dictionary or JSON object
    return predictions.to_dict(orient="records")
