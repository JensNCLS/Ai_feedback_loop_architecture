from pathlib import Path
import platform
import subprocess
import sys
import mlflow
import json
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
def retraining_first_reviewer():
    try:
        # Step 1: Load the processed data from previous DVC step
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / "media" / "raw_first_reviewer" / "feedback_images_first_reviewer.json"
        
        # Check if the JSON file exists
        if not json_path.exists():
            logger.error(f"First reviewer training data file not found at {json_path}")
            return {"status": "failure", "message": f"First reviewer training data file not found at {json_path}"}
            
        # Load the data from JSON file
        try:
            with open(json_path, 'r') as f:
                feedback_images = json.load(f)
            
            # Check if we have a valid list of feedback images
            if not isinstance(feedback_images, list):
                logger.error("First reviewer feedback images JSON is not a list")
                return {"status": "failure", "message": "First reviewer feedback images JSON is not a list"}
                
            if len(feedback_images) == 0:
                logger.info("No first reviewer images to train on, skipping training")
                return {"status": "success", "message": "No first reviewer images to train on", "count": 0}
                
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
            logger.error(f"Error loading first reviewer training data: {e}")
            return {"status": "failure", "message": f"Error loading first reviewer training data: {e}"}
        
        # Step 2: Run YOLOv5 training
        logger.info("Starting YOLOv5 training for first reviewer data")
        
        # Setup paths
        project_root = Path(__file__).parent.parent.parent.parent
        yolov5_dir = project_root / "yolov5"
        dataset_yaml = project_root / "media" / "dataset.yaml"
        output_dir = project_root / "media" / "runs" / "train_first_reviewer"
        weights_path = yolov5_dir / "best.pt"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build YOLOv5 training command
        cmd = [
            sys.executable,
            str(yolov5_dir / "train.py"),
            "--img", "640",
            "--batch", "8",
            "--epochs", "20",  # Same as original pipeline
            "--data", str(dataset_yaml),
            "--weights", str(weights_path),
            "--project", str(output_dir),
            "--name", "exp",
            "--workers", "2",
            "--cache",
            "--patience", "5"  # Early stopping: stop if no improvement after 5 epochs
        ]
        
        logger.info(f"Running training command: {' '.join(cmd)}")

        try:
            # Run with output capture to better diagnose issues
            process = subprocess.run(
                cmd,
                check=False,  # Handle return code manually
                capture_output=True,  # Capture output to diagnose issues
                text=True  # Convert output to text
            )
            
            if process.returncode != 0:
                logger.error(f"Training process failed with code {process.returncode}")
                logger.error(f"Error output: {process.stderr[:500]}...")  # Log first 500 chars of stderr
                
                # Check for memory-related errors
                if process.returncode == -9 or "out of memory" in process.stderr.lower() or "killed" in process.stderr.lower():
                    error_msg = "Training process was killed due to memory limitations. Try reducing batch size or image resolution."
                else:
                    error_msg = f"Training process failed with exit code {process.returncode}"
                
                return {
                    "status": "failure",
                    "message": error_msg,
                    "stderr": process.stderr[:1000]  # Include truncated stderr for debugging
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

                    with mlflow.start_run(run_name="feedback_first_reviewer_retraining") as run:
                        run_id = run.info.run_id

                        # Log parameters
                        mlflow.log_param("epochs", 20)  # Updated to match the new value
                        mlflow.log_param("batch_size", 8)  # Fixed to match actual batch size used in training
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
                            "skincancer_detection_model_first_reviewer"
                        )

                        logger.info(f"Registered model version: {registered_model.version}")

                        # Promote to Production
                        client = mlflow.tracking.MlflowClient()
                        client.transition_model_version_stage(
                            name="skincancer_detection_model_first_reviewer",
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
