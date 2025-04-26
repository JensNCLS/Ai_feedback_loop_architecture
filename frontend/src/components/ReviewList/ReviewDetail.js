import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import BoundingBox from '../ImageAnalysis/BoundingBox';
import { getScaledImageDimensions } from '../../utils/imageUtils';
import './ReviewDetail.css';

const ReviewDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Drawing state
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 });
  const [drawEnd, setDrawEnd] = useState({ x: 0, y: 0 });
  const [showDrawingBox, setShowDrawingBox] = useState(false);
  const [hoveredItem, setHoveredItem] = useState(null);

  const imageRef = useRef(null);
  const imageContainerRef = useRef(null);

  // Fetch review data
  useEffect(() => {
    const fetchReviewData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/review-items/${id}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch review data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Review data received:', data);
        console.log('Predictions received:', data.predictions);
        
        setReviewData(data);
        setPredictions(data.predictions || []);
        setReviewNotes(data.review_notes || '');
        setError('');
      } catch (err) {
        console.error('Error fetching review data:', err);
        setError(`Failed to load review data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchReviewData();
  }, [id]);

  // Calculate scaling factors for the image
  const getScalingFactors = () => {
    if (!imageRef.current) return { scaleX: 1, scaleY: 1 };
    
    const { naturalWidth, naturalHeight } = imageRef.current;
    const width = imageRef.current.clientWidth;
    const height = imageRef.current.clientHeight;
    
    return {
      scaleX: width / naturalWidth,
      scaleY: height / naturalHeight
    };
  };

  // Handle prediction selection
  const handlePredictionClick = (prediction, index) => {
    setSelectedPrediction({...prediction, index});
  };

  // Update a prediction
  const updatePrediction = (updatedValues) => {
    if (selectedPrediction === null) return;
    
    const updatedPredictions = [...predictions];
    updatedPredictions[selectedPrediction.index] = {
      ...updatedPredictions[selectedPrediction.index],
      ...updatedValues,
      modified: true
    };
    
    setPredictions(updatedPredictions);
    setSelectedPrediction({
      ...selectedPrediction,
      ...updatedValues,
      modified: true
    });
  };

  // Handle box dragging or resizing
  const handleBoxChange = (index, newBox) => {
    const updatedPredictions = [...predictions];
    updatedPredictions[index] = {
      ...updatedPredictions[index],
      ...newBox,
      modified: true
    };
    
    setPredictions(updatedPredictions);
    if (selectedPrediction?.index === index) {
      setSelectedPrediction({
        ...selectedPrediction,
        ...newBox,
        modified: true
      });
    }
  };

  // Remove a prediction
  const removePrediction = (index) => {
    const updatedPredictions = predictions.filter((_, i) => i !== index);
    setPredictions(updatedPredictions);
    setSelectedPrediction(null);
  };

  // Mouse handlers for drawing new boxes
  const handleMouseDown = (e) => {
    if (imageRef.current && 
        !isDrawing && 
        e.target === imageRef.current &&
        reviewData.status !== 'reviewed') {
      const containerRect = imageContainerRef.current.getBoundingClientRect();
      const x = e.clientX - containerRect.left;
      const y = e.clientY - containerRect.top;
      
      setDrawStart({ x, y });
      setDrawEnd({ x, y });
      setIsDrawing(true);
      setShowDrawingBox(true);
    }
  };

  const handleMouseMove = (e) => {
    if (isDrawing) {
      const containerRect = imageContainerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - containerRect.left, containerRect.width));
      const y = Math.max(0, Math.min(e.clientY - containerRect.top, containerRect.height));
      
      setDrawEnd({ x, y });
    }
  };

  const handleMouseUp = () => {
    if (isDrawing) {
      setIsDrawing(false);
      addNewBox();
    }
  };

  // Add a new bounding box
  const addNewBox = () => {
    if (!showDrawingBox || !imageRef.current) return;

    const imgElement = imageRef.current;
    const { naturalWidth, naturalHeight } = imgElement;
    const containerRect = imageContainerRef.current.getBoundingClientRect();
    
    // Convert drawing coordinates to natural image coordinates
    const scaleX = naturalWidth / containerRect.width;
    const scaleY = naturalHeight / containerRect.height;
    
    // Calculate the correct coordinates
    const startX = Math.min(drawStart.x, drawEnd.x);
    const startY = Math.min(drawStart.y, drawEnd.y);
    const endX = Math.max(drawStart.x, drawEnd.x);
    const endY = Math.max(drawStart.y, drawEnd.y);
    
    // Convert to image coordinates
    const xmin = startX * scaleX;
    const ymin = startY * scaleY;
    const xmax = endX * scaleX;
    const ymax = endY * scaleY;

    // Minimum size check (at least 10x10 pixels)
    if ((endX - startX) < 10 || (endY - startY) < 10) {
      setShowDrawingBox(false);
      return;
    }
    
    // Create a new prediction object
    const newPrediction = {
      xmin,
      ymin,
      xmax,
      ymax,
      name: "New Finding",
      confidence: 0.5,
      modified: true,
      isNew: true
    };
    
    // Add the new box to predictions
    const newIndex = predictions.length;
    setPredictions([...predictions, newPrediction]);
    setShowDrawingBox(false);
    
    // Select the newly added box
    setTimeout(() => handlePredictionClick(newPrediction, newIndex), 100);
  };

  // Calculate dimensions for the drawing box
  const drawingBoxStyle = {
    position: "absolute",
    left: `${Math.min(drawStart.x, drawEnd.x)}px`,
    top: `${Math.min(drawStart.y, drawEnd.y)}px`,
    width: `${Math.abs(drawEnd.x - drawStart.x)}px`,
    height: `${Math.abs(drawEnd.y - drawStart.y)}px`,
    border: "2px dashed #3498db",
    backgroundColor: "rgba(52, 152, 219, 0.2)",
    pointerEvents: "none",
    zIndex: 30
  };

  // Handle form submission
  const handleSubmitReview = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      const response = await fetch(`/api/review-items/${id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          predictions,
          review_notes: reviewNotes,
          status: 'reviewed'
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to submit review: ${response.status}`);
      }
      
      setSaveSuccess(true);
      setTimeout(() => {
        navigate('/review');
      }, 2000);
    } catch (err) {
      console.error('Error submitting review:', err);
      setError(`Failed to submit review: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="review-detail-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading review data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="review-detail-container">
        <div className="error-panel">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/review')} className="back-button">
            Back to Review List
          </button>
        </div>
      </div>
    );
  }

  if (!reviewData) {
    return (
      <div className="review-detail-container">
        <div className="error-panel">
          <h2>Review Not Found</h2>
          <p>The requested review could not be found.</p>
          <button onClick={() => navigate('/review')} className="back-button">
            Back to Review List
          </button>
        </div>
      </div>
    );
  }

  // Preparation for bounding boxes
  const { scaleX, scaleY } = getScalingFactors();

  return (
    <div className="review-detail-container">
      <div className="review-header">
        <button onClick={() => navigate('/review')} className="back-button">
          &larr; Back to List
        </button>
        <h1>Review Case #{id}</h1>
        <div className="case-status">
          Status: <span className={`status-indicator ${reviewData.status}`}>{reviewData.status}</span>
        </div>
      </div>

      <div className="review-content">
        <div className="image-panel">
          <div 
            className="image-container" 
            ref={imageContainerRef}
            style={{ position: "relative", cursor: reviewData.status !== 'reviewed' ? "crosshair" : "default" }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={isDrawing ? () => setIsDrawing(false) : undefined}
          >
            <img
              ref={imageRef}
              src={reviewData.image_url || '/placeholder-image.jpg'}
              alt={`Case ${id}`}
              className="review-image"
              onLoad={() => {
                // Force re-render to get correct scaling after image loads
                setPredictions([...predictions]);
              }}
            />
            
            {/* Drawing box */}
            {showDrawingBox && reviewData.status !== 'reviewed' && (
              <div style={drawingBoxStyle}></div>
            )}
            
            {/* Render bounding boxes on the image */}
            {predictions.map((pred, index) => (
              <BoundingBox
                key={index}
                pred={pred}
                index={index}
                scaleX={scaleX}
                scaleY={scaleY}
                isHovered={hoveredItem === index}
                handleBoxChange={reviewData.status !== 'reviewed' ? handleBoxChange : null}
                setHoveredItem={setHoveredItem}
                removeBox={reviewData.status !== 'reviewed' ? removePrediction : null}
              />
            ))}
          </div>
          
          {reviewData.feedback_text && (
            <div className="original-feedback-panel">
              <h3>Original Feedback</h3>
              <p>{reviewData.feedback_text}</p>
            </div>
          )}
        </div>
        
        <div className="review-panel">
          <div className="predictions-section">
            <h3>Dermatologist Predictions</h3>
            {/* Removed the unused boolean expression that was here: {reviewData.status !== 'reviewed'} */}
            <div className="predictions-list">
              {console.log('Rendering predictions list with:', predictions)}
              {predictions && predictions.length > 0 ? (
                predictions.map((pred, index) => (
                  <div
                    key={index}
                    className={`prediction-item ${selectedPrediction?.index === index ? 'selected' : ''} ${pred.modified ? 'modified' : ''}`}
                    onClick={() => handlePredictionClick(pred, index)}
                  >
                    <div className="prediction-header">
                      <span className="prediction-name">{pred.name}</span>
                      <span 
                        className={`prediction-confidence ${
                          pred.confidence > 0.7 ? 'high' : 
                          pred.confidence > 0.5 ? 'medium' : 'low'
                        }`}
                      >
                        {Math.round(pred.confidence * 100)}%
                      </span>
                    </div>
                    
                    <div className="prediction-actions">
                      {pred.modified && <span className="modified-badge">Modified</span>}
                      {pred.isNew && <span className="new-badge">New</span>}
                      {reviewData.status !== 'reviewed' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removePrediction(index);
                          }}
                          className="remove-btn"
                          title="Remove prediction"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-predictions">
                  No predictions available for this image
                </div>
              )}
            </div>
          </div>
          
          {selectedPrediction && reviewData.status !== 'reviewed' && (
            <div className="edit-prediction-panel">
              <h3>Edit Prediction</h3>
              <div className="edit-form">
                <div className="form-group">
                  <label>Finding Name:</label>
                  <input
                    type="text"
                    value={selectedPrediction.name}
                    onChange={(e) => updatePrediction({ name: e.target.value })}
                    className="input-field"
                  />
                </div>
                
                <div className="form-group">
                  <label>Confidence: {Math.round(selectedPrediction.confidence * 100)}%</label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={Math.round(selectedPrediction.confidence * 100)}
                    onChange={(e) => updatePrediction({ confidence: parseInt(e.target.value) / 100 })}
                    className="range-slider"
                  />
                </div>
              </div>
            </div>
          )}
          
          <form className="review-form" onSubmit={handleSubmitReview}>
            <h3>Second Review Notes</h3>
            <textarea
              className="review-notes"
              placeholder="Add your review notes here..."
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              disabled={reviewData.status === 'reviewed'}
            ></textarea>
            
            {reviewData.status !== 'reviewed' && (
              <button 
                type="submit" 
                className="submit-review-btn"
                disabled={saving}
              >
                {saving ? 'Submitting...' : 'Submit Second Review'}
              </button>
            )}
            
            {saveSuccess && (
              <div className="success-message">
                Review submitted successfully! Redirecting...
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReviewDetail;