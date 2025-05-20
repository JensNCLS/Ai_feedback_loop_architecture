import React from 'react';
import BoundingBox from './BoundingBox';
import { getScaledImageDimensions } from '../../utils/imageUtils';

const ImageViewer = ({
  imageUrl,
  analyzing,
  analysisStatus,
  predictions,
  imgRef,
  imageContainerRef,
  handleMouseDown,
  handleMouseMove,
  handleMouseUp,
  isDrawing,
  showDrawingBox,
  drawingBoxStyle,
  hoveredItem,
  setHoveredItem,
  handleBoxChange,
  removeBox,
  setIsDrawing
}) => {
  if (!imageUrl) {
    return <p style={{ fontSize: "16px", color: "#7f8c8d" }}>No image uploaded.</p>;
  }

  const noResultsNotification = analysisStatus === "completed" && predictions.length === 0 && (
    <div 
      style={{
        backgroundColor: "#d4edda",
        color: "#155724",
        padding: "10px 15px",
        borderRadius: "5px",
        marginBottom: "15px",
        textAlign: "center",
        width: "80%",
        maxWidth: "500px",
        border: "1px solid #c3e6cb"
      }}
    >
      <p style={{ margin: 0, fontWeight: "bold" }}>No lesions detected</p>
      <p style={{ margin: "5px 0 0 0", fontSize: "14px" }}>
        No abnormalities found in this image. You can still provide feedback.
      </p>
    </div>
  );

  const analyzingOverlay = analyzing && (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 10,
      }}
    >
      <div
        style={{
          width: "50px",
          height: "50px",
          border: "5px solid rgba(255, 255, 255, 0.3)",
          borderTop: "5px solid #3498db",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
        }}
      ></div>
      <div
        style={{
          position: "absolute",
          top: "60%",
          color: "white",
          fontWeight: "bold",
          textShadow: "1px 1px 3px rgba(0,0,0,0.7)",
        }}
      >
        Analyzing image...
      </div>
    </div>
  );

  const drawingBoxElement = showDrawingBox && !analyzing && (
    <div style={drawingBoxStyle}></div>
  );

  const boundingBoxes = predictions.map((pred, index) => {
    const { width, height, naturalWidth, naturalHeight } = getScaledImageDimensions(imgRef);
    
    const scaleX = width / naturalWidth;
    const scaleY = height / naturalHeight;
    
    return (
      <BoundingBox 
        key={index}
        pred={pred}
        index={index}
        scaleX={scaleX}
        scaleY={scaleY}
        isHovered={hoveredItem === index}
        handleBoxChange={handleBoxChange}
        setHoveredItem={setHoveredItem}
        removeBox={removeBox}
      />
    );
  });

  return (
    <>
      {noResultsNotification}
      <div
        ref={imageContainerRef}
        style={{
          position: "relative",
          width: "100%",
          maxWidth: "800px",
          cursor: analyzing ? "wait" : (analysisStatus === "completed" ? "crosshair" : "default")
        }}
        onMouseDown={analysisStatus === "completed" ? handleMouseDown : undefined}
        onMouseMove={analysisStatus === "completed" ? handleMouseMove : undefined}
        onMouseUp={analysisStatus === "completed" ? handleMouseUp : undefined}
        onMouseLeave={analysisStatus === "completed" && isDrawing ? () => setIsDrawing(false) : undefined}
      >
        <img
          ref={imgRef}
          src={imageUrl}
          alt="Uploaded"
          style={{
            width: "100%",
            height: "auto",
            display: "block",
            borderRadius: "10px",
            border: "2px solid #bdc3c7",
            filter: analyzing ? "brightness(0.7)" : "none",
          }}
        />
        
        {analyzingOverlay}
        {drawingBoxElement}
        {boundingBoxes}
      </div>
    </>
  );
};

export default ImageViewer;