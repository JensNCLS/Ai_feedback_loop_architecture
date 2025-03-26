import logging
import mlflow
import mlflow.pytorch
import torch
import torch.nn as nn
import time
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
        feedback = FeedbackImage.objects.filter(retrained=False).order_by('-feedback_given_at')[:10]
        feedback_data = [f.feedback_data for f in feedback]
        return feedback_data, feedback

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
        feedback_data, feedback = self.collect_feedback()
        if feedback_data:
            retrained_model_info = self.mock_retrain(feedback_data)
            self.update_feedback(feedback)
            return retrained_model_info
        else:
            return {"status": "failure", "message": "No feedback to retrain the model."}
