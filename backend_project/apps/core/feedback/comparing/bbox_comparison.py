import math
import numpy as np
from ...logging.logging import get_logger

logger = get_logger()

def log_method_call(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with arguments: {args} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Finished {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def calculate_iou(box1, box2):

    # Calculate coordinates of intersection
    x_min_inter = max(box1['xmin'], box2['xmin'])
    y_min_inter = max(box1['ymin'], box2['ymin'])
    x_max_inter = min(box1['xmax'], box2['xmax'])
    y_max_inter = min(box1['ymax'], box2['ymax'])
    
    # Check if there is an intersection
    if x_max_inter <= x_min_inter or y_max_inter <= y_min_inter:
        return 0.0
    
    # Calculate intersection area
    intersection_area = (x_max_inter - x_min_inter) * (y_max_inter - y_min_inter)
    
    # Calculate box areas
    box1_area = (box1['xmax'] - box1['xmin']) * (box1['ymax'] - box1['ymin'])
    box2_area = (box2['xmax'] - box2['xmin']) * (box2['ymax'] - box2['ymin'])
    
    # Calculate IoU
    union_area = box1_area + box2_area - intersection_area
    
    return intersection_area / union_area if union_area > 0 else 0.0

def calculate_ciou(box1, box2):

    # Calculate IoU
    iou = calculate_iou(box1, box2)

    logger.debug(f"IOU: {iou}")
    
    # Width and height of boxes (for aspect ratio term)
    w1 = box1['xmax'] - box1['xmin']
    h1 = box1['ymax'] - box1['ymin']
    w2 = box2['xmax'] - box2['xmin']
    h2 = box2['ymax'] - box2['ymin']
    
    # Calculate center points (for distance term)
    x1_center = (box1['xmin'] + box1['xmax']) / 2
    y1_center = (box1['ymin'] + box1['ymax']) / 2
    x2_center = (box2['xmin'] + box2['xmax']) / 2
    y2_center = (box2['ymin'] + box2['ymax']) / 2
    
    # Center distance term
    center_distance_squared = (x1_center - x2_center) ** 2 + (y1_center - y2_center) ** 2
    
    # Enclosing box diagonal
    enclosing_x_min = min(box1['xmin'], box2['xmin'])
    enclosing_y_min = min(box1['ymin'], box2['ymin'])
    enclosing_x_max = max(box1['xmax'], box2['xmax'])
    enclosing_y_max = max(box1['ymax'], box2['ymax'])
    enclosing_diagonal_squared = (enclosing_x_max - enclosing_x_min) ** 2 + (enclosing_y_max - enclosing_y_min) ** 2
    
    # Distance term
    distance_term = center_distance_squared / enclosing_diagonal_squared
    
    # Aspect ratio term
    arctan1 = math.atan(w1 / h1) if h1 > 0 else 0
    arctan2 = math.atan(w2 / h2) if h2 > 0 else 0
    v = (4 / (math.pi ** 2)) * ((arctan1 - arctan2) ** 2)
    alpha = v / (1 - iou + v) if iou < 1 else 0
    aspect_ratio_term = alpha * v
    
    # Calculate CIoU
    ciou = iou - distance_term - aspect_ratio_term
    
    return {
        'iou': iou,
        'distance_term': distance_term,
        'aspect_ratio_term': aspect_ratio_term,
        'ciou': ciou
    }

def compare_predictions(ai_predictions, feedback_predictions, threshold=0.5):
    
    matches = [] 
    missed_detections = [] 
    false_positives = [] 
    significant_differences = []
    
    # Create copy of lists to avoid modifying originals
    remaining_ai = list(ai_predictions)
    remaining_feedback = list(feedback_predictions)
    
    # Create matrix of CIoU scores between all boxes
    ciou_matrix = np.zeros((len(ai_predictions), len(feedback_predictions)))
    ciou_results = {}
    
    for i, ai_pred in enumerate(ai_predictions):
        for j, feedback_pred in enumerate(feedback_predictions):
            ciou_result = calculate_ciou(ai_pred, feedback_pred)
            ciou_matrix[i, j] = ciou_result['ciou']
            ciou_results[(i, j)] = ciou_result
    
    # Match predictions by highest CIoU
    while len(remaining_ai) > 0 and len(remaining_feedback) > 0:
        max_i, max_j = np.unravel_index(np.argmax(ciou_matrix), ciou_matrix.shape)
        max_ciou = ciou_matrix[max_i, max_j]
        
        # If best match is below threshold, no more good matches exist
        if max_ciou <= 0:
            break
            
        # Get the corresponding predictions
        ai_pred = ai_predictions[max_i]
        feedback_pred = feedback_predictions[max_j]
        
        # Add to appropriate category
        match_info = {
            'ai_prediction': ai_pred,
            'feedback_prediction': feedback_pred,
            'ciou': ciou_results[(max_i, max_j)]
        }
        
        matches.append(match_info)
        
        # Check if this match has significant differences
        if max_ciou < threshold:
            significant_differences.append(match_info)
            
        # Remove matched predictions from consideration
        ai_index = remaining_ai.index(ai_pred)
        feedback_index = remaining_feedback.index(feedback_pred)
        
        remaining_ai.pop(ai_index)
        remaining_feedback.pop(feedback_index)
        
        # Zero out this pair in the matrix to prevent rematching
        ciou_matrix[max_i, :] = 0
        ciou_matrix[:, max_j] = 0
    
    # Any remaining predictions are unmatched
    missed_detections = remaining_feedback
    false_positives = remaining_ai
    
    # Determine if the image needs review
    needs_review = (len(significant_differences) > 0 or
                   len(missed_detections) > 0)
    
    return {
        'matches': matches,
        'missed_detections': missed_detections,
        'false_positives': false_positives,
        'significant_differences': significant_differences,
        'needs_review': needs_review
    }

def flag_for_review_check(analyzed_image, feedback_image, threshold=0.5, confidence_threshold=0.75):
   
    
    ai_predictions = analyzed_image
    feedback_predictions = feedback_image
        
    # Run comparison
    comparison_result = compare_predictions(ai_predictions, feedback_predictions, threshold)
    
    # Add summary metrics
    comparison_result['summary'] = {
        'ai_prediction_count': len(ai_predictions),
        'feedback_prediction_count': len(feedback_predictions),
        'match_count': len(comparison_result['matches']),
        'significant_difference_count': len(comparison_result['significant_differences']),
        'missed_detection_count': len(comparison_result['missed_detections']),
        'false_positive_count': len(comparison_result['false_positives']),
    }
    
    # Classification differences (when boxes match but labels don't)
    classification_differences = []
    for match in comparison_result['matches']:
        ai_label = match['ai_prediction'].get('name', '').lower()
        feedback_label = match['feedback_prediction'].get('name', '').lower()
        
        if ai_label != feedback_label:
            classification_differences.append({
                'ai_prediction': match['ai_prediction'],
                'feedback_prediction': match['feedback_prediction'],
                'ai_label': ai_label,
                'feedback_label': feedback_label
            })
    
    comparison_result['classification_differences'] = classification_differences
    comparison_result['summary']['classification_difference_count'] = len(classification_differences)
    
    # Check for high-confidence predictions that were removed by humans
    high_confidence_removals = []
    for fp in comparison_result['false_positives']:
        confidence = fp.get('confidence', 0)
        if confidence >= confidence_threshold:
            high_confidence_removals.append({
                'ai_prediction': fp,
                'confidence': confidence
            })
    
    comparison_result['high_confidence_removals'] = high_confidence_removals
    comparison_result['summary']['high_confidence_removal_count'] = len(high_confidence_removals)
    
    # Refine review recommendation based on all factors
    comparison_result['needs_review'] = (
        len(comparison_result['significant_differences']) > 0 or
        len(comparison_result['missed_detections']) > 0 or
        len(classification_differences) > 0 or
        len(high_confidence_removals) > 0
    )
    
    return comparison_result