from ..logging.logging import get_logger
from pathlib import Path
import pandas as pd
from PIL import Image
from io import BytesIO
import random
from ..utils import get_image_from_minio
import json
import yaml
import numpy as np
import shutil
from sklearn.model_selection import KFold

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
def format_training_data():
    try:
        processed_count = 0
        class_names_set = set()
        
        base_dir = Path(__file__).parent.parent.parent.parent / "media"
        images_train_dir = base_dir / "images" / "train"
        images_val_dir = base_dir / "images" / "val"
        labels_train_dir = base_dir / "labels" / "train"
        labels_val_dir = base_dir / "labels" / "val"
        data_dir = base_dir / "raw"
        
        for dir_path in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        json_path = data_dir / "feedback_images.json"
        
        with open(json_path, 'r') as f:
            feedback_images = json.load(f)
        
        for feedback_image in feedback_images:
            try:
                if not feedback_image.get('feedback_data'):
                    logger.warning(f"No feedback data for image {feedback_image.get('id')}")
                    continue
                
                bucket_name = feedback_image.get('bucket_name')
                object_name = feedback_image.get('object_name')
                
                if not bucket_name or not object_name:
                    logger.warning(f"Missing MinIO information for feedback {feedback_image.get('id')}")
                    continue
                
                image_data = get_image_from_minio(
                    bucket_name,
                    object_name
                )
                
                if not image_data:
                    logger.warning(f"Failed to retrieve image from MinIO for preprocessed image {feedback_image['preprocessed_image_id']}")
                    continue
                
                img = Image.open(BytesIO(image_data))
                img_width, img_height = img.size
                
                is_train = random.random() < 0.8
                
                img_dir = images_train_dir if is_train else images_val_dir
                label_dir = labels_train_dir if is_train else labels_val_dir
                
                img_filename = f"{feedback_image['preprocessed_image_id']}.jpg"
                img_path = img_dir / img_filename
                
                with open(img_path, "wb") as f:
                    f.write(image_data)
                
                label_lines = []
                
                feedback_data = feedback_image['feedback_data']
                if not isinstance(feedback_data, list):
                    logger.error(f"Unexpected feedback data format for image {feedback_image['id']}")
                    logger.error(f"Raw feedback data: {feedback_data}")
                    continue
                
                for box in feedback_data:
                    try:
                        class_name = box.get("name", "unknown")
                        class_names_set.add(class_name)
                        class_id = box.get("class", 0)
                        
                        xmin = float(box.get("xmin", 0))
                        ymin = float(box.get("ymin", 0))
                        xmax = float(box.get("xmax", 0))
                        ymax = float(box.get("ymax", 0))
                        
                        center_x = (xmin + xmax) / (2.0 * img_width)
                        center_y = (ymin + ymax) / (2.0 * img_height)
                        width = (xmax - xmin) / img_width
                        height = (ymax - ymin) / img_height
                        
                        center_x = max(0, min(center_x, 1.0))
                        center_y = max(0, min(center_y, 1.0))
                        width = max(0, min(width, 1.0))
                        height = max(0, min(height, 1.0))
                        
                        label_lines.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                        logger.debug(f"Processed bounding box: {class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                    except Exception as e:
                        logger.error(f"Error processing bounding box: {e}")
                
                if label_lines:
                    label_filename = f"{feedback_image['preprocessed_image_id']}.txt"
                    label_path = label_dir / label_filename
                    
                    try:
                        with open(label_path, "w") as f:
                            f.write("\n".join(label_lines))
                    except Exception as e:
                        logger.error(f"Error writing label file {label_path}: {e}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing feedback image {feedback_image.get('id')}: {e}")
        
        class_names_list = list(class_names_set)

        return {
            "status": "success", 
            "message": f"Processed {processed_count} images for training", 
            "count": processed_count,
            "class_names": class_names_list,
            "feedback_images": feedback_images
        }
        
    except Exception as e:
        logger.error(f"Error in format_training_data: {e}")
        return {"status": "failure", "message": str(e), "count": 0}

@log_method_call
def format_training_data_kfold(k=5):
    try:
        processed_count = 0
        class_names_set = set()
        
        base_dir = Path(__file__).parent.parent.parent.parent / "media"
        kfold_dir = base_dir / "kfolds"
        data_dir = base_dir / "raw"
        
        # Clean up any existing kfolds directory
        if kfold_dir.exists():
            shutil.rmtree(kfold_dir)
        
        kfold_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = data_dir / "feedback_images.json"
        
        with open(json_path, 'r') as f:
            feedback_images = json.load(f)
        
        if len(feedback_images) < k:
            logger.warning(f"Not enough images for {k}-fold cross-validation. Using {len(feedback_images)} folds instead.")
            k = len(feedback_images)
        
        # Create the fold directories
        folds = []
        for i in range(k):
            fold_dir = kfold_dir / f"fold_{i}"
            fold_images_train_dir = fold_dir / "images" / "train"
            fold_images_val_dir = fold_dir / "images" / "val"
            fold_labels_train_dir = fold_dir / "labels" / "train"
            fold_labels_val_dir = fold_dir / "labels" / "val"
            
            for dir_path in [fold_images_train_dir, fold_images_val_dir, fold_labels_train_dir, fold_labels_val_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            folds.append({
                "dir": fold_dir,
                "images_train": fold_images_train_dir,
                "images_val": fold_images_val_dir,
                "labels_train": fold_labels_train_dir,
                "labels_val": fold_labels_val_dir
            })
        
        # Use scikit-learn's KFold for splitting
        kf = KFold(n_splits=k, shuffle=True, random_state=42)
        
        # Get indices for each fold
        indices = list(range(len(feedback_images)))
        fold_splits = list(kf.split(indices))
        
        # Assign fold to each image
        fold_assignments = {}
        for i, (train_idx, val_idx) in enumerate(fold_splits):
            for idx in val_idx:  # Images in val_idx will be validation for fold i
                feedback_images[idx]['fold'] = i
                fold_assignments[feedback_images[idx]['id']] = i
        
        # Process each image and assign to appropriate fold
        for feedback_image in feedback_images:
            try:
                if not feedback_image.get('feedback_data'):
                    logger.warning(f"No feedback data for image {feedback_image.get('id')}")
                    continue
                
                bucket_name = feedback_image.get('bucket_name')
                object_name = feedback_image.get('object_name')
                
                if not bucket_name or not object_name:
                    logger.warning(f"Missing MinIO information for feedback {feedback_image.get('id')}")
                    continue
                
                image_data = get_image_from_minio(
                    bucket_name,
                    object_name
                )
                
                if not image_data:
                    logger.warning(f"Failed to retrieve image from MinIO for preprocessed image {feedback_image['preprocessed_image_id']}")
                    continue
                
                img = Image.open(BytesIO(image_data))
                img_width, img_height = img.size
                
                # For each fold, decide if this image is in training or validation
                fold_id = feedback_image.get('fold', 0)
                
                for i in range(k):
                    # If this is the current fold, use for validation
                    # Otherwise, use for training
                    is_validation = (i == fold_id)
                    
                    fold = folds[i]
                    
                    img_dir = fold["images_val"] if is_validation else fold["images_train"]
                    label_dir = fold["labels_val"] if is_validation else fold["labels_train"]
                    
                    img_filename = f"{feedback_image['preprocessed_image_id']}.jpg"
                    img_path = img_dir / img_filename
                    
                    with open(img_path, "wb") as f:
                        f.write(image_data)
                    
                    label_lines = []
                    
                    feedback_data = feedback_image['feedback_data']
                    if not isinstance(feedback_data, list):
                        logger.error(f"Unexpected feedback data format for image {feedback_image['id']}")
                        logger.error(f"Raw feedback data: {feedback_data}")
                        continue
                    
                    for box in feedback_data:
                        try:
                            class_name = box.get("name", "unknown")
                            class_names_set.add(class_name)
                            class_id = box.get("class", 0)
                            
                            xmin = float(box.get("xmin", 0))
                            ymin = float(box.get("ymin", 0))
                            xmax = float(box.get("xmax", 0))
                            ymax = float(box.get("ymax", 0))
                            
                            center_x = (xmin + xmax) / (2.0 * img_width)
                            center_y = (ymin + ymax) / (2.0 * img_height)
                            width = (xmax - xmin) / img_width
                            height = (ymax - ymin) / img_height
                            
                            center_x = max(0, min(center_x, 1.0))
                            center_y = max(0, min(center_y, 1.0))
                            width = max(0, min(width, 1.0))
                            height = max(0, min(height, 1.0))
                            
                            label_lines.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                        except Exception as e:
                            logger.error(f"Error processing bounding box: {e}")
                    
                    if label_lines:
                        label_filename = f"{feedback_image['preprocessed_image_id']}.txt"
                        label_path = label_dir / label_filename
                        
                        try:
                            with open(label_path, "w") as f:
                                f.write("\n".join(label_lines))
                        except Exception as e:
                            logger.error(f"Error writing label file {label_path}: {e}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing feedback image {feedback_image.get('id')}: {e}")
        
        class_names_list = list(class_names_set)
        
        # Create dataset.yaml file for each fold
        for i, fold in enumerate(folds):
            dataset_yaml_path = fold["dir"] / "dataset.yaml"
            yaml_content = {
                "path": f"/app/media/kfolds/fold_{i}",  # Path should be adjusted for docker environment
                "train": "images/train",
                "val": "images/val", 
                "nc": len(class_names_list),
                "names": class_names_list
            }
            
            with open(dataset_yaml_path, "w") as f:
                yaml.dump(yaml_content, f, default_flow_style=False)

        return {
            "status": "success", 
            "message": f"Processed {processed_count} images into {k} folds for cross-validation using scikit-learn KFold", 
            "count": processed_count,
            "folds": k,
            "class_names": class_names_list,
            "feedback_images": feedback_images
        }
        
    except Exception as e:
        logger.error(f"Error in format_training_data_kfold: {e}")
        return {"status": "failure", "message": str(e), "count": 0}