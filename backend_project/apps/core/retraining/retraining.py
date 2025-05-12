import json
from PIL import Image
from io import BytesIO
import random
from pathlib import Path
import pathlib
import platform
import subprocess
import sys
import mlflow
import platform

from ..logging.logging import get_logger
from ..models import FeedbackImage
from ..utils import get_image_from_minio

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
def fetch_and_format_training_data():
    try:
        feedback_images = FeedbackImage.objects.filter(status='reviewed', retrained=False)
        
        if not feedback_images.exists():
            logger.info("No feedback images to process.")
            return {"status": "success", "message": "No feedback images to process."}
            
        # Create directories for YOLOv5 format if they don't exist
        base_dir = Path(__file__).parent.parent.parent.parent / "media"
        images_train_dir = base_dir / "images" / "train"
        images_val_dir = base_dir / "images" / "val"
        labels_train_dir = base_dir / "labels" / "train"
        labels_val_dir = base_dir / "labels" / "val"
        
        # Clean up existing files in the training directories
        for directory in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            # Remove all existing files in the directory
            for file_path in directory.glob("*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
            
        processed_count = 0
        class_names_set = set()
        
        # Process each feedback image
        for feedback_image in feedback_images:
            try:
                # Skip if no feedback data
                if not feedback_image.feedback_data:
                    logger.warning(f"No feedback data for image {feedback_image.id}")
                    continue
                    
                preprocessed_image = feedback_image.preprocessed_image
                if not preprocessed_image:
                    logger.warning(f"No preprocessed image for feedback {feedback_image.id}")
                    continue
                
                # Get image data from MinIO using preprocessedId
                image_data = get_image_from_minio(
                    preprocessed_image.bucket_name,
                    preprocessed_image.object_name
                )
                
                if not image_data:
                    logger.warning(f"Failed to retrieve image from MinIO for preprocessed image {preprocessed_image.id}")
                    continue
                
                # Load image to get dimensions
                img = Image.open(BytesIO(image_data))
                img_width, img_height = img.size
                
                # Split into train/val with 80/20 ratio
                is_train = random.random() < 0.8
                
                # Set image and label paths
                img_dir = images_train_dir if is_train else images_val_dir
                label_dir = labels_train_dir if is_train else labels_val_dir
                
                # Create unique filename using preprocessed image ID
                img_filename = f"{preprocessed_image.id}.jpg"
                img_path = img_dir / img_filename
                
                # Save image
                with open(img_path, "wb") as f:
                    f.write(image_data)
                
                # Create YOLOv5 format labels (class_id center_x center_y width height)
                label_lines = []
                
                for box in feedback_image.feedback_data:
                    try:
                        # Extract class name and bounding box coordinates
                        class_name = box.get("name", "unknown")
                        class_names_set.add(class_name)
                        
                        # Extract bounding box coordinates (ensure they are floats)
                        xmin = float(box.get("xmin", 0))
                        ymin = float(box.get("ymin", 0))
                        xmax = float(box.get("xmax", 0))
                        ymax = float(box.get("ymax", 0))
                        
                        # Convert to YOLOv5 format (normalized center_x, center_y, width, height)
                        center_x = (xmin + xmax) / (2.0 * img_width)
                        center_y = (ymin + ymax) / (2.0 * img_height)
                        width = (xmax - xmin) / img_width
                        height = (ymax - ymin) / img_height
                        
                        # Ensure values are within [0, 1]
                        center_x = max(0, min(center_x, 1.0))
                        center_y = max(0, min(center_y, 1.0))
                        width = max(0, min(width, 1.0))
                        height = max(0, min(height, 1.0))
                        
                        # Temporarily use 0 as class_id (we'll update this later)
                        # Will be replaced after we have all class names
                        label_lines.append(f"0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                    except Exception as e:
                        logger.error(f"Error processing bounding box: {e}")
                    
                    logger.info(label_lines)
                
                if label_lines:
                    # Create label file with same base name but .txt extension
                    label_filename = f"{preprocessed_image.id}.txt"
                    label_path = label_dir / label_filename
                    
                    with open(label_path, "w") as f:
                        f.write("\n".join(label_lines))
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing feedback image {feedback_image.id}: {e}")
    
        # Create class mapping and update label files
        class_mapping = {name: idx for idx, name in enumerate(sorted(class_names_set))}

        # Create YAML config file for YOLOv5
        yaml_path = base_dir / "dataset.yaml"
        with open(yaml_path, "w") as f:
            yaml_content = {
                "path": str(base_dir),
                "train": str(images_train_dir.relative_to(base_dir)),
                "val": str(images_val_dir.relative_to(base_dir)),
                "nc": len(class_mapping),
                "names": list(class_mapping.keys())
            }
            json.dump(yaml_content, f, indent=2)

        # Update all label files with correct class IDs
        for label_dir in [labels_train_dir, labels_val_dir]:
            for label_file in label_dir.glob("*.txt"):
                with open(label_file, "r") as f:
                    lines = f.readlines()

                updated_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:  # Ensure valid label format
                        class_name = parts[0]  # Temporarily stored as class name
                        class_id = class_mapping.get(class_name, 0)
                        updated_lines.append(f"{class_id} {' '.join(parts[1:])}")

                with open(label_file, "w") as f:
                    f.write("\n".join(updated_lines))
        
        # Convert class_names_set to a list before returning or using it
        class_names_list = list(class_names_set)

        return {
            "status": "success", 
            "message": f"Processed {processed_count} images for training", 
            "count": processed_count,
            "class_names": class_names_list,
            "feedback_images": feedback_images
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_and_format_training_data: {e}")
        return {"status": "failure", "message": str(e), "count": 0}

@log_method_call
def retraining():
    try:
        # Step 1: Prepare training data
        data_results = fetch_and_format_training_data()
        
        if data_results.get("status") == "failure":
            logger.error(f"Data preparation failed: {data_results.get('message')}")
            return data_results
            
        if data_results.get("count", 0) == 0:
            logger.info("No images to train on, skipping training")
            return data_results
        
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
            process = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info("Training completed successfully")
            logger.debug(f"Training stdout: {process.stdout}")

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
