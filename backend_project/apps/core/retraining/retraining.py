from pathlib import Path
import platform
import subprocess
import sys
import mlflow
import json
import yaml  # For YAML file parsing
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

@log_method_call
def retraining():
    try:
        # Step 1: Load the processed data from previous DVC step
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / "media" / "raw" / "feedback_images.json"
        
        # Check if the JSON file exists
        if not json_path.exists():
            logger.error(f"Training data file not found at {json_path}")
            return {"status": "failure", "message": f"Training data file not found at {json_path}"}
            
        # Load the data from JSON file
        try:
            with open(json_path, 'r') as f:
                feedback_images = json.load(f)
            
            # Check if we have a valid list of feedback images
            if not isinstance(feedback_images, list):
                logger.error("Feedback images JSON is not a list")
                return {"status": "failure", "message": "Feedback images JSON is not a list"}
                
            if len(feedback_images) == 0:
                logger.info("No images to train on, skipping training")
                return {"status": "success", "message": "No images to train on", "count": 0}
                
            # Create a data_results dictionary with feedback images and metadata
            data_results = {
                "status": "success",
                "count": len(feedback_images),
                "feedback_images": feedback_images,
                "class_names": []
            }
            
            # Extract unique class names from feedback data
            class_names = set()
            for img in feedback_images:
                if img.get("feedback_data"):
                    for box in img.get("feedback_data", []):
                        if box.get("name"):
                            class_names.add(box.get("name"))
            
            data_results["class_names"] = list(class_names)
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return {"status": "failure", "message": f"Error loading training data: {e}"}
        
        # Step 2: Run YOLOv5 training
        logger.info("Starting YOLOv5 training")
        
        # Setup paths
        project_root = Path(__file__).parent.parent.parent.parent
        yolov5_dir = project_root / "yolov5"
        dataset_yaml = project_root / "media" / "dataset.yaml"
        output_dir = project_root / "media" / "runs" / "train"
        weights_path = yolov5_dir / "best.pt"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build YOLOv5 training command
        cmd = [
            sys.executable,
            str(yolov5_dir / "train.py"),
            "--img", "640",
            "--batch", "16",
            "--epochs", "5",
            "--data", str(dataset_yaml),
            "--weights", str(weights_path),
            "--project", str(output_dir),
            "--name", "exp",
            "--exist-ok"
        ]

        logger.info(f"Running training command: {' '.join(cmd)}")

        try:
            # Run without capturing stdout/stderr to avoid binary data issues
            process = subprocess.run(
                cmd,
                check=False,  # Handle return code manually
                capture_output=False  # Don't capture output
            )
            
            if process.returncode != 0:
                logger.error(f"Training process failed with code {process.returncode}")
                return {
                    "status": "failure",
                    "message": f"Training process failed with exit code {process.returncode}"
                }
                
            logger.info("Training completed successfully")

            # Find latest exp folder
            def get_latest_exp_dir(base_dir):
                exp_dirs = list(Path(base_dir).glob("exp*"))
                return max(exp_dirs, key=lambda d: d.stat().st_mtime)

            exp_dir = get_latest_exp_dir(output_dir)
            weights_dir = exp_dir / "weights"
            best_model_path = None

            if weights_dir.exists():
                pt_files = list(weights_dir.glob("*.pt"))
                if pt_files:
                    best_model_path = pt_files[0]

            # MLflow logging
            if best_model_path:
                try:
                    mlflow.set_tracking_uri("http://mlflow:5000")

                    with mlflow.start_run(run_name="feedback_retraining") as run:
                        run_id = run.info.run_id

                        # Log parameters
                        mlflow.log_param("epochs", 5)
                        mlflow.log_param("batch_size", 16)
                        mlflow.log_param("image_size", 640)
                        mlflow.log_param("images_processed", data_results.get("count", 0))
                        mlflow.log_param("class_names", str(data_results.get("class_names", [])))
                        mlflow.log_param("python_version", platform.python_version())
                        mlflow.log_param("system_platform", platform.platform())

                        # Log the best model
                        mlflow.log_artifact(output_dir / "exp" / "results.png")

                        # Log other artifacts
                        for file_name in ["results.png", "opt.yaml", "hyp.yaml"]:
                            file_path = exp_dir / file_name
                            if file_path.exists():
                                mlflow.log_artifact(str(file_path))

                        if weights_dir.exists():
                            mlflow.log_artifacts(str(weights_dir), artifact_path="weights")

                


                

                        # Register model
                        model_uri = f"runs:/{run_id}/weights/{best_model_path.name}"
                        registered_model = mlflow.register_model(
                            model_uri,
                            "skincancer_detection_model"
                        )

                        logger.info(f"Registered model version: {registered_model.version}")

                        # Promote to Production
                        client = mlflow.tracking.MlflowClient()
                        client.transition_model_version_stage(
                            name="skincancer_detection_model",
                            version=registered_model.version,
                            stage="Production"
                        )

                        # Mark feedback images as retrained
                    #for feedback_image in data_results.get("feedback_images", []):
                    #    feedback_image.retrained = True
                     #   feedback_image.save()

                    return {
                        "status": "success",
                        "message": "Model training completed and registered in MLflow",
                        "mlflow_run_id": run_id,
                        "model_version": registered_model.version,
                        "images_processed": data_results.get("count", 0)
                    }

                except Exception as e:
                    logger.error(f"Error logging model to MLflow: {e}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Training process failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return {
                "status": "failure",
                "message": f"Training process failed: {e}",
                "stderr": e.stderr
            }

    except Exception as e:
        logger.error(f"Error in retraining: {e}")
        return {"status": "failure", "message": str(e)}