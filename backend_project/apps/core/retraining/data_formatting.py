from ..logging.logging import get_logger
from pathlib import Path
import pandas as pd
from PIL import Image
from io import BytesIO
import random
from ..utils import get_image_from_minio
import json

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
        
        # Define paths
        base_dir = Path(__file__).parent.parent.parent.parent / "media"
        images_train_dir = base_dir / "images" / "train"
        images_val_dir = base_dir / "images" / "val"
        labels_train_dir = base_dir / "labels" / "train"
        labels_val_dir = base_dir / "labels" / "val"
        data_dir = base_dir / "raw"
        
        # Create necessary directories
        for dir_path in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Read the JSON file that contains feedback image data
        json_path = data_dir / "feedback_images.json"
        
        with open(json_path, 'r') as f:
            feedback_images = json.load(f)
        
        # Process each feedback image from the JSON
        for feedback_image in feedback_images:
            try:
                # Skip if no feedback data
                if not feedback_image.get('feedback_data'):
                    logger.warning(f"No feedback data for image {feedback_image.get('id')}")
                    continue
                
                # Get MinIO credentials directly from JSON
                bucket_name = feedback_image.get('bucket_name')
                object_name = feedback_image.get('object_name')
                
                if not bucket_name or not object_name:
                    logger.warning(f"Missing MinIO information for feedback {feedback_image.get('id')}")
                    continue
                
                # Get image data from MinIO
                image_data = get_image_from_minio(
                    bucket_name,
                    object_name
                )
                
                if not image_data:
                    logger.warning(f"Failed to retrieve image from MinIO for preprocessed image {feedback_image['preprocessed_image_id']}")
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
                img_filename = f"{feedback_image['preprocessed_image_id']}.jpg"
                img_path = img_dir / img_filename
                
                # Save image
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
                        
                        # Store class name with coordinates for later class ID assignment
                        # Format: class_name center_x center_y width height
                        label_lines.append(f"0 {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")
                    except Exception as e:
                        logger.error(f"Error processing bounding box: {e}")
                
                if label_lines:
                    # Create label file with same base name but .txt extension
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
    
        # Create class mapping and update label files
        class_mapping = {name: idx for idx, name in enumerate(sorted(class_names_set))}

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