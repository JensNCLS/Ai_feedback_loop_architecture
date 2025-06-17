from pathlib import Path
import platform
import subprocess
import sys
import mlflow
import json
import pandas as pd
import numpy as np
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
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / "media" / "raw_first_reviewer" / "feedback_images_first_reviewer.json"
        
        if not json_path.exists():
            logger.error(f"First reviewer training data file not found at {json_path}")
            return {"status": "failure", "message": f"First reviewer training data file not found at {json_path}"}
            
        try:
            with open(json_path, 'r') as f:
                feedback_images = json.load(f)
            
            if not isinstance(feedback_images, list):
                logger.error("First reviewer feedback images JSON is not a list")
                return {"status": "failure", "message": "First reviewer feedback images JSON is not a list"}
                
            if len(feedback_images) == 0:
                logger.info("No first reviewer images to train on, skipping training")
                return {"status": "success", "message": "No first reviewer images to train on", "count": 0}
                
            data_results = {
                "status": "success",
                "count": len(feedback_images),
                "feedback_images": feedback_images,
                "class_names": []
            }
            
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
        
        logger.info("Starting YOLOv5 training for first reviewer data")
        
        project_root = Path(__file__).parent.parent.parent.parent
        yolov5_dir = project_root / "yolov5"
        dataset_yaml = project_root / "media" / "dataset.yaml"
        output_dir = project_root / "media" / "runs" / "train_first_reviewer"
        weights_path = yolov5_dir / "best.pt"
        
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(yolov5_dir / "train.py"),
            "--img", "640",
            "--batch", "8",
            "--epochs", "20",
            "--data", str(dataset_yaml),
            "--weights", str(weights_path),
            "--project", str(output_dir),
            "--name", "exp",
            "--workers", "2",
            "--cache",
            "--patience", "5"
        ]
        
        logger.info(f"Running training command: {' '.join(cmd)}")

        try:
            process = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"Training process failed with code {process.returncode}")
                logger.error(f"Error output: {process.stderr[:500]}...")
                
                if process.returncode == -9 or "out of memory" in process.stderr.lower() or "killed" in process.stderr.lower():
                    error_msg = "Training process was killed due to memory limitations. Try reducing batch size or image resolution."
                else:
                    error_msg = f"Training process failed with exit code {process.returncode}"
                
                return {
                    "status": "failure",
                    "message": error_msg,
                    "stderr": process.stderr[:1000]
                }
                
            logger.info("Training completed successfully")

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

            if best_model_path:
                try:
                    mlflow.set_tracking_uri("http://mlflow:5000")

                    with mlflow.start_run(run_name="feedback_first_reviewer_retraining") as run:
                        run_id = run.info.run_id

                        # Log parameters
                        mlflow.log_param("epochs", 20)
                        mlflow.log_param("batch_size", 8) 
                        mlflow.log_param("image_size", 640)
                        mlflow.log_param("images_processed", data_results.get("count", 0))
                        mlflow.log_param("class_names", str(data_results.get("class_names", [])))
                        mlflow.log_param("python_version", platform.python_version())
                        mlflow.log_param("system_platform", platform.platform())

                        mlflow.log_artifact(output_dir / "exp" / "results.png")

                        for file_name in ["results.png", "opt.yaml", "hyp.yaml"]:
                            file_path = exp_dir / file_name
                            if file_path.exists():
                                mlflow.log_artifact(str(file_path))

                        if weights_dir.exists():
                            mlflow.log_artifacts(str(weights_dir), artifact_path="weights")

                        model_uri = f"runs:/{run_id}/weights/{best_model_path.name}"
                        registered_model = mlflow.register_model(
                            model_uri,
                            "skincancer_detection_model_first_reviewer"
                        )

                        logger.info(f"Registered model version: {registered_model.version}")

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

@log_method_call
def retraining_first_reviewer_kfold(k=7, epochs=20, batch_size=8, img_size=640, patience=5):
    """
    Performs k-fold cross-validation training on first reviewer data.
    For each fold:
    - Trains a model using the fold's dataset
    - Collects metrics
    - Returns average metrics across all folds
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        kfolds_dir = project_root / "media" / "kfolds_first_reviewer"
        
        if not kfolds_dir.exists():
            logger.error("K-folds directory for first reviewer not found. Run format_first_reviewer_data_kfold first.")
            return {
                "status": "failure", 
                "message": "K-folds directory for first reviewer not found. Run format_first_reviewer_data_kfold first."
            }
        
        fold_dirs = list(kfolds_dir.glob("fold_*"))
        if not fold_dirs:
            logger.error("No fold directories found in the first reviewer kfolds directory.")
            return {
                "status": "failure", 
                "message": "No fold directories found in the first reviewer kfolds directory."
            }
        
        fold_count = len(fold_dirs)
        if fold_count != k:
            logger.warning(f"Found {fold_count} folds, but {k} were requested. Using {fold_count} folds.")
            k = fold_count
        
        yolov5_dir = project_root / "yolov5"
        weights_path = yolov5_dir / "best.pt"
        output_base_dir = project_root / "media" / "runs" / "kfold_first_reviewer"
        output_base_dir.mkdir(parents=True, exist_ok=True)
        results_csv_path = output_base_dir / "kfold_results.csv"
        
        all_metrics = []
        fold_run_ids = []
        
        mlflow.set_tracking_uri("http://mlflow:5000")

        with mlflow.start_run(run_name=f"first_reviewer_kfold_cv_{k}_folds") as parent_run:
            parent_run_id = parent_run.info.run_id
            
            # Log k-fold parameters
            mlflow.log_param("k_folds", k)
            mlflow.log_param("epochs", epochs)
            mlflow.log_param("batch_size", batch_size)
            mlflow.log_param("image_size", img_size)
            mlflow.log_param("patience", patience)
            
            # Train on each fold
            for i in range(k):
                fold_dir = kfolds_dir / f"fold_{i}"
                dataset_yaml = fold_dir / "dataset.yaml"
                
                if not dataset_yaml.exists():
                    logger.error(f"Dataset YAML not found for first reviewer fold {i}.")
                    continue
                
                # Create output directory for this fold
                fold_output_dir = output_base_dir / f"fold_{i}"
                fold_output_dir.mkdir(parents=True, exist_ok=True)
                
                # Build the training command
                cmd = [
                    sys.executable,
                    str(yolov5_dir / "train.py"),
                    "--img", str(img_size),
                    "--batch", str(batch_size),
                    "--epochs", str(epochs),
                    "--data", str(dataset_yaml),
                    "--weights", str(weights_path),
                    "--project", str(fold_output_dir),
                    "--name", "exp",
                    "--workers", "2",
                    "--cache",
                    "--patience", str(patience)
                ]
                
                logger.info(f"Running first reviewer training command for fold {i}: {' '.join(cmd)}")
                
                try:
                    process = subprocess.run(
                        cmd,
                        check=False,
                        capture_output=True,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        logger.error(f"First reviewer training process for fold {i} failed with code {process.returncode}")
                        logger.error(f"Error output: {process.stderr[:500]}...")
                        continue
                    
                    logger.info(f"First reviewer training for fold {i} completed successfully")
                    
                    # Get the experiment directory
                    def get_latest_exp_dir(base_dir):
                        exp_dirs = list(base_dir.glob("exp*"))
                        if not exp_dirs:
                            return None
                        return max(exp_dirs, key=lambda d: d.stat().st_mtime)
                    
                    exp_dir = get_latest_exp_dir(fold_output_dir)
                    if not exp_dir:
                        logger.error(f"No experiment directory found for first reviewer fold {i}")
                        continue
                    
                    # Log metrics from this fold's training
                    with mlflow.start_run(run_name=f"first_reviewer_fold_{i}_training", nested=True) as fold_run:
                        fold_run_id = fold_run.info.run_id
                        fold_run_ids.append(fold_run_id)
                        
                        # Log fold-specific parameters
                        mlflow.log_param("fold", i)
                        mlflow.log_param("epochs", epochs)
                        mlflow.log_param("batch_size", batch_size)
                        mlflow.log_param("image_size", img_size)
                        
                        # Log files from experiment
                        weights_dir = exp_dir / "weights"
                        best_model_path = None
                        
                        if weights_dir.exists():
                            pt_files = list(weights_dir.glob("*.pt"))
                            if pt_files:
                                best_model_path = pt_files[0]
                        
                        if best_model_path:
                            # Log weights
                            mlflow.log_artifact(str(best_model_path), "weights")
                        
                        # Log metrics
                        results_csv = exp_dir / "results.csv"
                        if results_csv.exists():
                            try:
                                logger.info(f"Reading results CSV from: {results_csv}")
                                results_df = pd.read_csv(results_csv)
                                logger.info(f"Found columns: {list(results_df.columns)}")
                                
                                # Find and fix column names - handle spacing differences
                                column_names = results_df.columns
                                map_col = next(col for col in column_names if "metrics/mAP_0.5" in col and "0.95" not in col)
                                map_range_col = next(col for col in column_names if "metrics/mAP_0.5:0.95" in col)
                                precision_col = next(col for col in column_names if "metrics/precision" in col)
                                recall_col = next(col for col in column_names if "metrics/recall" in col)
                                val_box_loss_col = next(col for col in column_names if "val/box_loss" in col)
                                val_obj_loss_col = next(col for col in column_names if "val/obj_loss" in col)
                                val_cls_loss_col = next(col for col in column_names if "val/cls_loss" in col)
                                
                                # Get the best metrics (highest mAP)
                                best_epoch = results_df[map_col].idxmax()
                                best_metrics = results_df.iloc[best_epoch]
                                
                                # Extract all the metrics we care about
                                fold_metrics = {
                                    "fold": i,
                                    "mAP_0.5": best_metrics[map_col],
                                    "mAP_0.5:0.95": best_metrics[map_range_col],
                                    "precision": best_metrics[precision_col],
                                    "recall": best_metrics[recall_col],
                                    "val_loss": best_metrics[val_box_loss_col] + best_metrics[val_obj_loss_col] + best_metrics[val_cls_loss_col],
                                    "best_epoch": best_epoch
                                }
                                
                                # Add to the combined metrics
                                all_metrics.append(fold_metrics)
                                
                                # Log the metrics to MLflow
                                for key, value in fold_metrics.items():
                                    if key != "fold":
                                        mlflow.log_metric(key, value)
                                
                                # Log results.csv and other artifacts
                                mlflow.log_artifact(str(results_csv))
                                
                                for file_name in ["results.png", "opt.yaml", "hyp.yaml", "confusion_matrix.png"]:
                                    file_path = exp_dir / file_name
                                    if file_path.exists():
                                        mlflow.log_artifact(str(file_path))
                                
                            except Exception as e:
                                logger.error(f"Error processing first reviewer results for fold {i}: {e}")
                                import traceback
                                logger.error(f"Traceback: {traceback.format_exc()}")
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"First reviewer training process for fold {i} failed: {e}")
                    logger.error(f"Error output: {e.stderr}")
                    continue
            
            # Calculate and log average metrics
            if all_metrics:
                metrics_df = pd.DataFrame(all_metrics)
                
                # Save results to CSV
                metrics_df.to_csv(results_csv_path, index=False)
                mlflow.log_artifact(str(results_csv_path))
                
                # Calculate averages
                avg_metrics = {
                    "avg_mAP_0.5": metrics_df["mAP_0.5"].mean(),
                    "avg_mAP_0.5:0.95": metrics_df["mAP_0.5:0.95"].mean(),
                    "avg_precision": metrics_df["precision"].mean(),
                    "avg_recall": metrics_df["recall"].mean(),
                    "avg_val_loss": metrics_df["val_loss"].mean(),
                    "std_mAP_0.5": metrics_df["mAP_0.5"].std(),
                    "std_mAP_0.5:0.95": metrics_df["mAP_0.5:0.95"].std(),
                    "std_precision": metrics_df["precision"].std(),
                    "std_recall": metrics_df["recall"].std()
                }
                
                # Log averaged metrics to parent run
                for key, value in avg_metrics.items():
                    mlflow.log_metric(key, value)
                
                # Determine best fold
                best_fold_idx = metrics_df["mAP_0.5"].idxmax()
                best_fold = int(metrics_df.iloc[best_fold_idx]["fold"])
                mlflow.log_metric("best_fold", best_fold)
                
                return {
                    "status": "success",
                    "message": f"Successfully completed first reviewer {len(all_metrics)}/{k} fold cross-validation",
                    "total_folds": k,
                    "folds_completed": len(all_metrics),
                    "avg_metrics": avg_metrics,
                    "best_fold": best_fold,
                    "results_csv": str(results_csv_path),
                    "fold_run_ids": fold_run_ids,
                    "parent_run_id": parent_run_id
                }
            else:
                return {
                    "status": "failure",
                    "message": "No first reviewer folds were successfully trained",
                    "total_folds": k,
                    "folds_completed": 0
                }
        
    except Exception as e:
        logger.error(f"Error in retraining_first_reviewer_kfold: {e}")
        return {"status": "failure", "message": str(e)}
