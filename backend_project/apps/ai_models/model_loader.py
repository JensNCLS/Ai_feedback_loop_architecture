import torch
from PIL import Image
from io import BytesIO
from pathlib import Path
import pathlib

# Force WindowsPath to behave as PosixPath in Linux-based containers
pathlib.WindowsPath = pathlib.PosixPath

# Resolve the model path
model_path = Path(__file__).parent / "best.pt"

# Check if the model file exists
if not model_path.is_file():
    raise FileNotFoundError(f"Model file not found at {model_path}")

# Convert the path to a string for compatibility
model_path = str(model_path)

# Load the YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)

# Set the model to run on the CPU
model.to(torch.device("cpu"))

# Analyze a single image
def analyze_image(image_file):
    image = Image.open(BytesIO(image_file))  # Convert the uploaded file to a PIL image
    results = model(image)  # Run inference on the image
    predictions = results.pandas().xyxy[0]  # Extract predictions in xyxy format
    return predictions.to_dict(orient="records")  # Return predictions as a dictionary