import React, { useState, useRef, useEffect } from 'react';
import { spinnerKeyframes } from '../../utils/imageUtils';
import ImageUploader from './ImageUploader';
import HelpPanel from './HelpPanel';
import PredictionsList from './PredictionsList';
import ImageViewer from './ImageViewer';
import FeedbackCommit from '../FeedbackCommit';
import { CLASS_NAMES, getClassNumber } from '../../utils/classUtils';

function ImageAnalysis() {
  const [image, setImage] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");
  const [preprocessedImageId, setPreprocessedImageId] = useState(null);
  const [analyzedImageId, setAnalyzedImageId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [hoveredItem, setHoveredItem] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState({ x: 0, y: 0 });
  const [drawEnd, setDrawEnd] = useState({ x: 0, y: 0 });
  const [showDrawingBox, setShowDrawingBox] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [tempName, setTempName] = useState("");
  const [tempConfidence, setTempConfidence] = useState(50);
  
  const imgRef = useRef(null);
  const imageContainerRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setImageUrl(URL.createObjectURL(file));
      setPredictions([]);
      setError("");
      setPreprocessedImageId(null);
      setAnalysisStatus("");
      setAnalyzedImageId(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!image) {
      setError("Please select an image to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("image", image);

    try {
      setLoading(true);
      const response = await fetch("/api/upload/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Backend response:", data);

        setPreprocessedImageId(data.preprocessed_image_id);
        setAnalysisStatus("in_progress");
        setAnalyzing(true);
        setError("");
      } else {
        const errorMessage = `Failed to upload image. Status: ${response.status}`;
        console.error(errorMessage);
        setError(errorMessage);
      }
    } catch (err) {
      console.error("Error during upload:", err);
      setError("An error occurred while uploading the image.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!preprocessedImageId) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/check_analysis_status/${preprocessedImageId}/`
        );
        const data = await response.json();

        if (data.success) {
          if (data.status === "completed") {
            setPredictions(
              data.analysis_results.map((pred) => ({
                ...pred,
                isModified: false,
              }))
            );
            setAnalyzedImageId(data.analyzed_image_id);
            setAnalysisStatus("completed");
            setAnalyzing(false);
            clearInterval(intervalId);
          } else {
            setAnalysisStatus("in_progress");
          }
        }
      } catch (error) {
        console.error("Error checking analysis status:", error);
        setError("An error occurred while checking the analysis status.");
        setAnalyzing(false);
        clearInterval(intervalId);
      }
    }, 500);

    return () => clearInterval(intervalId);
  }, [preprocessedImageId]);

  const handleBoxChange = (index, newBox) => {
    setPredictions((prevPredictions) =>
      prevPredictions.map((pred, i) =>
        i === index ? { ...pred, ...newBox, isModified: true } : pred
      )
    );
  };

  const startEditing = (index, pred) => {
    setEditingItem(index);
    setTempName(pred.name);
    setTempConfidence(pred.confidence * 100);
  };


  const saveEditing = () => {
    if (editingItem === null) return;

    const className = tempName || CLASS_NAMES[0];
    const classNumber = getClassNumber(className);

    setPredictions(prevPredictions => 
      prevPredictions.map((pred, i) => 
        i === editingItem 
          ? { 
              ...pred, 
              name: className,
              class: classNumber,
              confidence: Math.max(0, Math.min(100, tempConfidence)) / 100, 
              isModified: true 
            } 
          : pred
      )
    );
    
    setEditingItem(null);
  };

  const addNewBox = () => {
    if (!showDrawingBox) return;
    
    const imgElement = imgRef.current;
    const { naturalWidth, naturalHeight } = imgElement;
    const containerRect = imageContainerRef.current.getBoundingClientRect();
    
    const scaleX = naturalWidth / containerRect.width;
    const scaleY = naturalHeight / containerRect.height;
    
    const startX = Math.min(drawStart.x, drawEnd.x);
    const startY = Math.min(drawStart.y, drawEnd.y);
    const endX = Math.max(drawStart.x, drawEnd.x);
    const endY = Math.max(drawStart.y, drawEnd.y);
    
    const xmin = startX * scaleX;
    const ymin = startY * scaleY;
    const xmax = endX * scaleX;
    const ymax = endY * scaleY;

    if ((endX - startX) < 10 || (endY - startY) < 10) {
      setShowDrawingBox(false);
      return;
    }
    
    const defaultClassName = CLASS_NAMES[0];
    const newPrediction = {
      xmin,
      ymin,
      xmax,
      ymax,
      name: defaultClassName,
      class: 0,
      confidence: 0.5,
      isModified: true,
      isNew: true
    };
    
    const newIndex = predictions.length;
    setPredictions([...predictions, newPrediction]);
    setShowDrawingBox(false);
    
    setTimeout(() => startEditing(newIndex, newPrediction), 100);
  };

  const removeBox = (index) => {
    setPredictions(predictions.filter((_, i) => i !== index));
    if (editingItem === index) {
      setEditingItem(null);
    }
  };

  const handleMouseDown = (e) => {
    if (imageUrl && 
        !analyzing && 
        !isDrawing && 
        e.target === imgRef.current &&
        analysisStatus === "completed") {
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

  const drawingBoxStyle = {
    position: "absolute",
    left: Math.min(drawStart.x, drawEnd.x),
    top: Math.min(drawStart.y, drawEnd.y),
    width: Math.abs(drawEnd.x - drawStart.x),
    height: Math.abs(drawEnd.y - drawStart.y),
    border: "2px dashed #3498db",
    backgroundColor: "rgba(52, 152, 219, 0.2)",
    pointerEvents: "none",
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        height: "100vh",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <style>{spinnerKeyframes}</style>
      
      {/* Left Sidebar: Upload Section */}
      <div
        style={{
          width: "20%",
          padding: "20px",
          borderRight: "1px solid #bdc3c7",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <ImageUploader 
          handleImageChange={handleImageChange}
          handleSubmit={handleSubmit}
          error={error}
          loading={loading}
        />
        
        {/* Help panel */}
        {imageUrl && analysisStatus === "completed" && (
          <HelpPanel showHelp={showHelp} setShowHelp={setShowHelp} />
        )}
        
        {/* Predictions List */}
        <PredictionsList
          predictions={predictions}
          editingItem={editingItem}
          hoveredItem={hoveredItem}
          tempName={tempName}
          setTempName={setTempName}
          tempConfidence={tempConfidence}
          setTempConfidence={setTempConfidence}
          saveEditing={saveEditing}
          removeBox={removeBox}
          startEditing={startEditing}
          setEditingItem={setEditingItem}
          setHoveredItem={setHoveredItem}
        />
      </div>

      {/* Center: Image Display */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          position: "relative",
        }}
      >
        {loading ? (
          <div style={{ fontSize: "18px", color: "#3498db", fontWeight: "bold" }}>
            Loading...
          </div>
        ) : (
          <ImageViewer
            imageUrl={imageUrl}
            analyzing={analyzing}
            analysisStatus={analysisStatus}
            predictions={predictions}
            imgRef={imgRef}
            imageContainerRef={imageContainerRef}
            handleMouseDown={handleMouseDown}
            handleMouseMove={handleMouseMove}
            handleMouseUp={handleMouseUp}
            isDrawing={isDrawing}
            showDrawingBox={showDrawingBox}
            drawingBoxStyle={drawingBoxStyle}
            hoveredItem={hoveredItem}
            setHoveredItem={setHoveredItem}
            handleBoxChange={handleBoxChange}
            removeBox={removeBox}
            setIsDrawing={setIsDrawing}
          />
        )}
      </div>

      {/* Right Sidebar: Feedback Section */}
      <div
        style={{
          width: "20%",
          padding: "20px",
          borderLeft: "1px solid #bdc3c7",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <h2 style={{ fontSize: "20px", marginBottom: "20px" }}>Feedback</h2>
        {analysisStatus === "completed" && predictions.length > 0 && (
          <FeedbackCommit
            predictions={predictions}
            preprocessedImageId={preprocessedImageId}
            analyzedImageId={analyzedImageId}
          />
        )}
      </div>
    </div>
  );
}

export default ImageAnalysis;