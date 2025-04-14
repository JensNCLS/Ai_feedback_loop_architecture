import logging
import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import time
import os
import subprocess
from pathlib import Path
from PIL import Image
from io import BytesIO
from ..models import FeedbackImage
from ..logging.logging import get_logger

logger = get_logger()

def log_method_call(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with arguments: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            if isinstance(result, dict) and result.get("status") == "failure":
                logger.warning(f"Warning from {func.__name__}: {result.get('message')}")
            logger.info(f"Finished {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

class MockModel(nn.Module):
    def __init__(self):
        super(MockModel, self).__init__()
        self.layer = nn.Linear(1, 1)  # A simple linear layer

    def forward(self, x):
        return self.layer(x)

class Model_retrainer:
    def __init__(self):
        self.retrained = False

    @log_method_call
    def collect_feedback(self):
        feedback_images = FeedbackImage.objects.filter(retrained=False)
        feedback_data = []

        # Ensure YOLOv5 directory structure exists
        os.makedirs("data/images/train", exist_ok=True)
        os.makedirs("data/labels/train", exist_ok=True)

        for feedback in feedback_images:
            # Extract feedback data
            image_path = f"data/images/train/{feedback.preprocessed_image.id}.jpg"
            label_path = f"data/labels/train/{feedback.preprocessed_image.id}.txt"

            # Save the image
            with open(image_path, "wb") as img_file:
                img_file.write(feedback.preprocessed_image.image)

            # Extract image dimensions using Pillow
            image = Image.open(BytesIO(feedback.preprocessed_image.image))
            width, height = image.size

            # Save the annotations in YOLO format
            with open(label_path, "w") as label_file:
                for box in feedback.feedback_data:
                    class_id = box["class"]  # Use the correct key for the class ID
                    x_center = (box["xmin"] + box["xmax"]) / 2
                    y_center = (box["ymin"] + box["ymax"]) / 2
                    width_box = box["xmax"] - box["xmin"]
                    height_box = box["ymax"] - box["ymin"]

                    # Normalize coordinates (0 to 1)
                    x_center /= width
                    y_center /= height
                    width_box /= width
                    height_box /= height

                    label_file.write(f"{class_id} {x_center} {y_center} {width_box} {height_box}\n")

            feedback_data.append(feedback)

        return feedback_data

    @log_method_call
    def mock_retrain(self, feedback_data):
        time.sleep(3)

        # Create a mock PyTorch model
        model = MockModel()

        # Log metrics and parameters to MLflow
        with mlflow.start_run():
            mlflow.log_param("feedback_count", len(feedback_data))
            mlflow.log_metric("accuracy", 0.85)  # Replace with actual accuracy
            mlflow.log_metric("precision", 0.80)  # Replace with actual precision
            mlflow.log_metric("recall", 0.75)  # Replace with actual recall

            # Save the mock PyTorch model
            mlflow.pytorch.log_model(model, "model")

        retrained_model_info = {"status": "success", "message": "Model retrained with feedback data."}
        return retrained_model_info

    @log_method_call
    def update_feedback(self, feedback):
        for f in feedback:
            f.retrained = True
            f.save()

    @log_method_call
    def retrain_model(self):
        feedback_data = self.collect_feedback()
        if feedback_data:
            try:
                # Trigger YOLOv5 retraining
                self.retrain_yolov5()

                # Mark feedback as retrained
                self.update_feedback(feedback_data)

                return {"status": "success", "message": "Model retrained with feedback data."}
            except Exception as e:
                logger.error(f"Retraining failed: {e}")
                return {"status": "failure", "message": f"Retraining failed: {e}"}
        else:
            return {"status": "failure", "message": "No feedback to retrain the model."}

    def mark_feedback_as_retrained(self, feedback_data):
        for feedback in feedback_data:
            feedback.retrained = True
            feedback.save()

    @log_method_call
    def retrain_yolov5(self):
        command = [
            "python", "yolov5/train.py",
            "--img", "640",  # Image size
            "--batch", "16",  # Batch size
            "--epochs", "50",  # Number of epochs
            "--data", "data.yaml",  # Path to dataset configuration
            "--weights", "apps/ai_models/best.pt",  # Path to the pre-trained model
            "--cache"
        ]
        subprocess.run(command, check=True)
