import torch
from PIL import Image
from io import BytesIO
from pathlib import Path

model_path = Path("D:/Fontys/Master/Semester 1 herstart/Ai_feedback_loop_architecture/backend/apps/ai_models/best.pt")
model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(model_path), force_reload=True)


# Function to analyze a single image passed from FastAPI directly
def analyze_image(image_file):
    # Convert the uploaded file to a PIL image
    image = Image.open(BytesIO(image_file))

    # Run inference on the image using YOLOv5
    results = model(image)

    # Extract predictions as a DataFrame
    predictions = results.pandas().xyxy[0]  # Extract predictions in xyxy format

    # Return predictions as a dictionary or JSON object
    return predictions.to_dict(orient="records")

