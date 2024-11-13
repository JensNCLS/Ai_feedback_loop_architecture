import torch
from pathlib import Path

# Path to your custom-trained .pt file
model_path = 'best.pt'

# Load your custom YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)


# Function to analyze multiple data in a directory
def analyze_images_in_folder(folder_path):
    # Get a list of all image files in the folder (e.g., .jpg, .png)
    image_paths = list(Path(folder_path).glob("*.jpg")) + list(Path(folder_path).glob("*.png"))

    for image_path in image_paths:
        # Run inference on each image
        results = model(str(image_path))

        # Display and save results for each image
        results.print()  # Print detected objects
        results.save()  # Save results with bounding boxes
        results.show()  # Show image with bounding boxes

        # Extract predictions as a DataFrame
        predictions = results.pandas().xyxy[0]
        print(f"Results for {image_path.name}:")
        print(predictions)


# Folder containing data
folder_path = '../../data/raw_images'
analyze_images_in_folder(folder_path)
