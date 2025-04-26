from ..logging.logging import get_logger
from ..models import FeedbackImage
import json
from PIL import Image
from io import BytesIO
import random
import os
import mlflow
import shutil
from pathlib import Path
import subprocess
import sys
from datetime import datetime
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
def gather_training_data():
    try:
        
        feedback_images = FeedbackImage.objects.filter(retrained=False).select_related('preprocessed_image')

        training_data = []

        for feedback in feedback_images:
            preprocessed_image = feedback.preprocessed_image
            training_data.append({
                "feedback_data": feedback.feedback_data,
                "image": preprocessed_image.image,
                "original_filename": preprocessed_image.original_filename
            })

        return training_data

    except Exception as e:
        logger.error(f"Error while gathering training data: {e}")
        raise

@log_method_call
def format_to_yolo(training_data):
    try: 
        yolo_formatted_data = []
        
        for item in training_data:
            image_binary = item["image"]
            original_filename = item["original_filename"]
            
            if isinstance(item["feedback_data"], str):
                feedback_data = json.loads(item["feedback_data"])
            else:
                feedback_data = item["feedback_data"]
                
            if not feedback_data:
                continue
                
            image = Image.open(BytesIO(image_binary))
            image_width, image_height = image.size
            
            yolo_annotations = []
            
            for box in feedback_data:
                class_id = box.get("class", 0)
                
                xmin = float(box.get("xmin", 0))
                ymin = float(box.get("ymin", 0))
                xmax = float(box.get("xmax", 0))
                ymax = float(box.get("ymax", 0))
                
                x_center = (xmin + xmax) / 2 / image_width
                y_center = (ymin + ymax) / 2 / image_height
                width = (xmax - xmin) / image_width
                height = (ymax - ymin) / image_height
                
                # Ensure values are within [0, 1]
                x_center = max(0, min(1, x_center))
                y_center = max(0, min(1, y_center))
                width = max(0, min(1, width))
                height = max(0, min(1, height))
                
                yolo_annotations.append({
                    "class_id": class_id,
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height
                })
            
            if yolo_annotations:
                yolo_formatted_data.append({
                    "image_binary": image_binary,
                    "original_filename": original_filename,
                    "image_width": image_width,
                    "image_height": image_height,
                    "annotations": yolo_annotations
                })
        
        logger.info(yolo_formatted_data)
        return yolo_formatted_data
        
    except Exception as e:
        logger.error(f"Error formatting data to YOLO format: {e}")
        raise

@log_method_call
def save_yolo_data(formatted_data, dataset_dir=None, split_ratio=0.8, overwrite_yaml=False):
    try:
        import os
        import shutil
        from pathlib import Path
        from PIL import Image
        from io import BytesIO
        
        # Set up the directory structure for Docker environment
        if dataset_dir is None:
            base_dir = Path("/app/yolov5/data/feedback_dataset")
        else:
            base_dir = Path(dataset_dir)
        
        # Define directory paths
        images_train_dir = base_dir / "images" / "train"
        images_val_dir = base_dir / "images" / "val"
        labels_train_dir = base_dir / "labels" / "train"
        labels_val_dir = base_dir / "labels" / "val"
        
        # Create directories if they don't exist
        for dir_path in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Clear existing directories to start fresh
        for dir_path in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
            logger.info(f"Clearing directory: {dir_path}")
            for item in dir_path.glob("*"):
                if item.is_file():
                    item.unlink()  # Remove files
                elif item.is_dir():
                    shutil.rmtree(item)  # Remove directories recursively
        
        # Get unique class IDs
        class_ids = set()
        
        # Process each formatted data item
        for i, data in enumerate(formatted_data):
            # Generate a unique filename
            original_filename = data["original_filename"]
            filename_base = f"{i:04d}_{original_filename.split('.')[0]}"
            image_filename = f"{filename_base}.jpg"
            label_filename = f"{filename_base}.txt"
            
            # Decide whether to put in train or validation set
            is_train = random.random() < split_ratio
            
            if is_train:
                image_dir = images_train_dir
                label_dir = labels_train_dir
            else:
                image_dir = images_val_dir
                label_dir = labels_val_dir
            
            # Save the image properly using PIL instead of writing raw binary data
            image_path = image_dir / image_filename
            try:
                # Open the image using PIL
                img = Image.open(BytesIO(data["image_binary"]))
                # Convert to RGB if needed (handles RGBA or other formats)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Save as JPEG with standard format and ensure the file is flushed/closed properly
                img.save(str(image_path), format='JPEG', quality=95)
                img.close()  # Explicitly close the image to free up memory 
            except Exception as e:
                logger.warning(f"Failed to save image {image_filename}: {e}")
                continue
            
            # Prepare label file content
            label_lines = []
            
            for annotation in data["annotations"]:
                class_id = annotation["class_id"]
                class_ids.add(class_id)
                x_center = annotation["x_center"]
                y_center = annotation["y_center"]
                width = annotation["width"]
                height = annotation["height"]
                
                # Add to label lines
                label_lines.append(f"{class_id} {x_center} {y_center} {width} {height}")
            
            # Save the label file
            label_path = label_dir / label_filename
            with open(label_path, 'w') as f:
                f.write('\n'.join(label_lines))
        
        # Create or update YAML configuration file
        yaml_path = base_dir / "dataset.yaml"
        
        # Check if YAML file already exists and respect the overwrite flag
        if not yaml_path.exists() or overwrite_yaml:
            # Create YAML configuration file
            yaml_content = f"""# YOLOv5 dataset configuration
train: {str(images_train_dir)}
val: {str(images_val_dir)}
test: # test images (optional)

# Classes
nc: {len(class_ids)}  # number of classes
names: [{"".join(f"'{i}', " for i in range(len(class_ids)))[:-2]}]  # class names by index
"""
            
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)
        
        # Mark feedback images as retrained
        feedback_ids = []
        for data in formatted_data:
            if hasattr(data, 'id'):
                feedback_ids.append(data.id)
        
        if feedback_ids:
            FeedbackImage.objects.filter(id__in=feedback_ids).update(retrained=True)
        
        # Prepare the return information
        return {
            "base_dir": str(base_dir),
            "yaml_path": str(yaml_path),
            "directories": {
                "images": {
                    "train": str(images_train_dir),
                    "val": str(images_val_dir)
                },
                "labels": {
                    "train": str(labels_train_dir),
                    "val": str(labels_val_dir)
                }
            },
            "image_count": len(formatted_data)
        }
        
    except Exception as e:
        logger.error(f"Error saving YOLO data: {e}")
        raise

@log_method_call
def train_model_with_mlflow(dataset_info, epochs=5, img_size=1280, batch_size=8, weights=None, experiment_name="model_retraining_feedback_data"):
    try:
        # Set default weights to YOLOv5s if not provided
        if weights is None:
            weights = "yolov5s.pt"
        
        # Try different possible paths for YOLOv5
        possible_paths = [
            Path("/app/yolov5"),      # Docker container path
            Path(__file__).parents[4] / "yolov5"  # Project root path
        ]
        
        # Find the first valid path
        yolov5_dir = None
        for path in possible_paths:
            if path.exists() and (path / "train.py").exists():
                yolov5_dir = path
                break
                
        if yolov5_dir is None:
            # If no valid path is found, default to the expected Docker path
            yolov5_dir = Path("/app/yolov5")
        
        if yolov5_dir.exists():
            train_script = yolov5_dir / "train.py"
        
        # Ensure YOLOv5 directory exists
        if not yolov5_dir.exists():
            raise FileNotFoundError(f"YOLOv5 directory not found at {yolov5_dir}")
            
        # Ensure train script exists
        train_script = yolov5_dir / "train.py"
        if not train_script.exists():
            raise FileNotFoundError(f"YOLOv5 train script not found at {train_script}")
        
        # Get the yaml configuration path
        yaml_path = dataset_info["yaml_path"]
        
        # Print the content of the YAML file for debugging
        if Path(yaml_path).exists():
            with open(yaml_path, 'r') as f:
                yaml_content = f.read()

            logger.info("YAML configuration content!!!")
        
        # Get timestamp for the run name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"feedback_train_{timestamp}"
        
        # Build the command with memory-safe settings
        cmd = [
            sys.executable,
            str(train_script),
            "--img", str(img_size),
            "--batch", str(batch_size),
            "--epochs", str(epochs),
            "--data", str(yaml_path),
            "--weights", str(weights),
            "--name", run_name,
            "--workers", "2",  # Reduce number of workers to avoid memory issues
            "--cache", "ram",  # Use RAM for caching instead of disk
        ]

        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Run the command with more verbose output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=str(yolov5_dir)  # Set working directory to yolov5 dir
        )

        logger.info("Training process started")
        
        # Stream and log the output in real-time
        stdout_lines = []
        stderr_lines = []
        
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            
            if stdout_line == '' and stderr_line == '' and process.poll() is not None:
                break
            
            if stdout_line:
                stdout_lines.append(stdout_line)
            
            if stderr_line:
                stderr_lines.append(stderr_line)

        logger.info("STDERR AND STDOUT!!!")
        
        # Get the return code
        return_code = process.poll()
        
        # Collect all output
        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)

        logger.info("OUTPUTS COLLECTED!!!")

        logger.info(return_code)
        logger.info(stderr)
        
        # Check for errors
        if return_code != 0:
            error_msg = f"YOLOv5 training failed with exit code {return_code}. Error: {stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Also check if the best weights file was created, which indicates successful training
        best_weights = yolov5_dir / "runs" / "train" / run_name / "weights" / "best.pt"
        if not best_weights.exists():
            error_msg = "YOLOv5 training did not produce weights file. Check logs for details."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        # Get the path to results.csv
        results_file = yolov5_dir / "runs" / "train" / run_name / "results.csv"

        logger.info("Training completed successfully")
        
        # Try to initialize MLflow, but don't fail if it doesn't work
        mlflow_available = False
        mlflow_error = None
        run_id = None
        mlflow_url = None
        
        try:
            # Configure MLflow
            mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
            mlflow.set_tracking_uri(mlflow_uri)
            
            # Set or create the experiment
            mlflow.set_experiment(experiment_name)
            
            logger.info("MLflow experiment created")
            mlflow_available = True
        except Exception as e:
            logger.warning(f"Could not initialize MLflow: {e}")
            mlflow_error = str(e)
        
        # If MLflow is available, try to log the results
        if mlflow_available:
            try:
                with mlflow.start_run(run_name=run_name) as run:
                    run_id = run.info.run_id
                    logger.info(f"MLflow run started with id: {run_id}")
                    
                    # Log parameters
                    try:
                        mlflow.log_params({
                            "epochs": epochs,
                            "img_size": img_size,
                            "batch_size": batch_size,
                            "weights": weights,
                            "yaml_config": yaml_path,
                            "image_count": dataset_info.get("image_count", 0)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to log parameters: {e}")
                    
                    # Log outputs to MLflow - Ensure we're only logging text data, not binary
                    try:
                        safe_stdout = ''.join(c for c in stdout if c.isprintable() or c in ['\n', '\t', '\r'])
                        safe_stderr = ''.join(c for c in stderr if c.isprintable() or c in ['\n', '\t', '\r'])
                        
                        # Create artifacts directory
                        output_dir = Path("train_logs")
                        output_dir.mkdir(exist_ok=True)
                        
                        with open(output_dir / "stdout.txt", "w", encoding="utf-8") as f:
                            f.write(safe_stdout)
                        
                        with open(output_dir / "stderr.txt", "w", encoding="utf-8") as f:
                            f.write(safe_stderr)
                        
                        # Log the files as artifacts instead of as parameters
                        mlflow.log_artifacts(str(output_dir))
                    except Exception as e:
                        logger.warning(f"Failed to log output files: {e}")
                        
                    # Log metrics from results.csv if available
                    try:
                        if results_file.exists():
                            import pandas as pd
                            results_df = pd.read_csv(results_file)
                            
                            # Get the best metrics (highest mAP)
                            best_row = results_df.iloc[results_df['metrics/mAP_0.5'].argmax()]
                            
                            # Log best metrics
                            for column in results_df.columns:
                                if column != 'epoch':  # Skip epoch as it's not a metric
                                    mlflow.log_metric(column, float(best_row[column]))
                            
                            # Log results as artifact
                            mlflow.log_artifact(str(results_file))
                    except Exception as e:
                        logger.warning(f"Failed to log metrics: {e}")
                    
                    # Log model if available
                    try:
                        if best_weights.exists():
                            # Copy the model to a safe location before logging as artifact
                            # This prevents issues with binary data handling
                            temp_model_dir = Path("temp_model")
                            temp_model_dir.mkdir(exist_ok=True)
                            temp_model_path = temp_model_dir / "best.pt"
                            shutil.copy2(str(best_weights), str(temp_model_path))
                            
                            # Log the copied model file as artifact
                            mlflow.log_artifact(str(temp_model_path), "model")
                    except Exception as e:
                        logger.warning(f"Failed to log model artifact: {e}")
                        
                    # Try to register the model in MLflow
                    try:
                        model_uri = f"runs:/{run_id}/model/best.pt"
                        mlflow.register_model(model_uri, "skin_cancer_detection")
                    except Exception as e:
                        logger.warning(f"Failed to register model: {e}")
                        
                    # Log confusion matrix and other plots if available
                    try:
                        plots_dir = yolov5_dir / "runs" / "train" / run_name
                        for plot_file in plots_dir.glob("*.png"):
                            mlflow.log_artifact(str(plot_file), "plots")
                    except Exception as e:
                        logger.warning(f"Failed to log plots: {e}")
                        
                    mlflow_url = f"{mlflow_uri}/#/experiments/{mlflow.get_experiment_by_name(experiment_name).experiment_id}/runs/{run_id}"
                    logger.info(f"MLflow tracking URL: {mlflow_url}")
            
            except Exception as e:
                logger.warning(f"Error during MLflow logging: {e}")
                mlflow_error = str(e)
        
        # Return successful training results, even if MLflow failed
        return {
            "status": "success",
            "run_id": run_id,
            "run_name": run_name,
            "best_weights": str(best_weights) if best_weights.exists() else None,
            "mlflow_url": mlflow_url,
            "mlflow_available": mlflow_available,
            "mlflow_error": mlflow_error
        }
    
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        return {
            "status": "failure",
            "message": str(e)
        }

@log_method_call
def deploy_model(training_result):
    try:
        import shutil
        import requests
        from pathlib import Path
        
        # Check if training was successful
        if training_result.get("status") != "success":
            return {
                "status": "failure",
                "message": f"Cannot deploy model: Training was not successful. {training_result.get('message', '')}"
            }
        
        # Get the path to the best weights from training
        best_weights_path = training_result.get("best_weights")
        if not best_weights_path or not Path(best_weights_path).exists():
            return {
                "status": "failure",
                "message": "Best weights file not found"
            }
        
        # Get the path to the AI models directory (shared volume between containers)
        ai_models_dir = Path(__file__).parents[3] / "ai_models"
        
        # Destination path for the model
        model_dest_path = ai_models_dir / "best.pt"
        
        # Backup the current model if it exists
        if model_dest_path.exists():
            backup_path = ai_models_dir / f"best_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
            shutil.copy2(model_dest_path, backup_path)
        
        # Copy the new model to the destination
        shutil.copy2(best_weights_path, model_dest_path)
        
        # Update model metadata
        metadata = {
            "deployed_at": datetime.now().isoformat(),
            "mlflow_run_id": training_result.get("run_id"),
            "mlflow_url": training_result.get("mlflow_url"),
            "model_source": best_weights_path
        }
        
        metadata_path = ai_models_dir / "model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Try to trigger model reload in the AI Models service
        try:
            # The AI model service might have an endpoint to reload the model
            response = requests.post(
                "http://ai_models:8001/reload-model/", 
                timeout=5
            )
            if response.status_code == 200:
                logger.info("Successfully triggered model reload in AI service")
            else:
                logger.warning(f"Model reload request failed with status code: {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not trigger model reload: {e}")
            logger.info("The model will be loaded on the next restart of the AI service")
        
        return {
            "status": "success",
            "message": f"Model successfully deployed to {model_dest_path}",
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        return {
            "status": "failure",
            "message": str(e)
        }

@log_method_call
def retrain_model(epochs=5, img_size=1280, batch_size=8, weights=None):
    try:
        # Step 1: Gather training data
        logger.info("Starting retraining process - gathering training data")
        training_data = gather_training_data()
        
        if not training_data:
            return {
                "status": "skipped",
                "message": "No new feedback data available for retraining"
            }
        
        # Step 2: Format data to YOLO format
        logger.info(f"Formatting {len(training_data)} feedback items to YOLO format")
        formatted_data = format_to_yolo(training_data)
        
        if not formatted_data:
            return {
                "status": "skipped",
                "message": "No valid annotations found in feedback data"
            }
        
        # Step 3: Save data to disk in YOLO format
        logger.info(f"Saving {len(formatted_data)} formatted items to disk")
        dataset_info = save_yolo_data(formatted_data, overwrite_yaml=True)

        logger.info(f"DATASET!!!!!! {dataset_info}")
        
        # Step 4: Train model with MLFlow tracking
        logger.info("Starting model training with MLFlow tracking")
        training_result = train_model_with_mlflow(
            dataset_info=dataset_info,
            epochs=epochs,
            img_size=img_size,
            batch_size=batch_size,
            weights=weights
        )
        
        if training_result.get("status") != "success":
            return {
                "status": "failure",
                "message": f"Training failed: {training_result.get('message', 'Unknown error')}",
                "training_result": training_result
            }
        
        # Step 5: Deploy the new model
        logger.info("Deploying new model")
        deployment_result = deploy_model(training_result)
        
        return {
            "status": "success",
            "message": "Model successfully retrained and deployed",
            "dataset_info": dataset_info,
            "training_result": training_result,
            "deployment_result": deployment_result,
            "feedback_count": len(training_data),
            "mlflow_url": training_result.get("mlflow_url")
        }
        
    except Exception as e:
        logger.error(f"Error during model retraining workflow: {e}")
        return {
            "status": "failure",
            "message": str(e)
        }

