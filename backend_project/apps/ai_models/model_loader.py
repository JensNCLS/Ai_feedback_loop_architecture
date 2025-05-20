import torch
from PIL import Image
from io import BytesIO
from pathlib import Path
import pathlib

pathlib.WindowsPath = pathlib.PosixPath

model_path = Path(__file__).parent / "best.pt"

if not model_path.is_file():
    raise FileNotFoundError(f"Model file not found at {model_path}")

model_path = str(model_path)

model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)

model.to(torch.device("cpu"))


def analyze_image(image_file):
    image = Image.open(BytesIO(image_file))
    results = model(image)
    predictions = results.pandas().xyxy[0]
    return predictions.to_dict(orient="records")