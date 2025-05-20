import React from 'react';
import { CLASS_NAMES } from '../../utils/classUtils';

const PredictionItem = ({ 
  pred, 
  index, 
  isEditing, 
  isHovered,
  tempName, 
  setTempName, 
  tempConfidence, 
  setTempConfidence,
  saveEditing,
  cancelEditing,
  removeBox,
  startEditing,
  handleHover
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: isEditing ? "column" : "row",
        justifyContent: "space-between",
        padding: "8px 5px",
        fontSize: "14px",
        alignItems: isEditing ? "stretch" : "center",
        backgroundColor: 
          isHovered ? "rgba(52, 152, 219, 0.1)" : 
          pred.isModified ? "#f8f9fa" : "transparent",
        borderRadius: "3px",
        transition: "background-color 0.2s",
        cursor: isEditing ? "default" : "pointer",
        position: "relative",
        borderBottom: "1px solid #efefef"
      }}
      onMouseEnter={() => handleHover(index)}
      onMouseLeave={() => handleHover(null)}
      onClick={() => !isEditing && startEditing(index, pred)}
    >
      {isEditing ? (
        <>
          <div style={{ marginBottom: "8px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#7f8c8d", marginBottom: "2px" }}>
              Finding Type:
            </label>
            <select
              value={tempName}
              onChange={(e) => setTempName(e.target.value)}
              style={{
                width: "100%",
                padding: "4px 6px",
                border: "1px solid #bdc3c7",
                borderRadius: "3px",
                fontSize: "13px",
                backgroundColor: "white"
              }}
              autoFocus
            >
              {CLASS_NAMES.map((className, idx) => (
                <option key={idx} value={className}>
                  {className} (Class {idx})
                </option>
              ))}
            </select>
          </div>
          
          <div style={{ marginBottom: "8px" }}>
            <label style={{ display: "block", fontSize: "12px", color: "#7f8c8d", marginBottom: "2px" }}>
              Confidence: {tempConfidence.toFixed(1)}%
            </label>
            <input
              type="range"
              min="1"
              max="100"
              value={tempConfidence}
              onChange={(e) => setTempConfidence(parseFloat(e.target.value))}
              style={{ width: "100%" }}
            />
          </div>
          
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                saveEditing();
              }}
              style={{
                padding: "4px 10px",
                backgroundColor: "#2ecc71",
                color: "white",
                border: "none",
                borderRadius: "3px",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: "bold"
              }}
            >
              Save
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                cancelEditing();
              }}
              style={{
                padding: "4px 10px",
                backgroundColor: "#95a5a6",
                color: "white",
                border: "none",
                borderRadius: "3px",
                cursor: "pointer",
                fontSize: "12px"
              }}
            >
              Cancel
            </button>
            
            <button 
              onClick={(e) => {
                e.stopPropagation();
                removeBox(index);
              }}
              style={{
                padding: "4px 10px",
                backgroundColor: "#e74c3c",
                color: "white",
                border: "none",
                borderRadius: "3px",
                cursor: "pointer",
                fontSize: "12px"
              }}
            >
              Remove
            </button>
          </div>
        </>
      ) : (
        // View Mode UI
        <>
          <div style={{ fontWeight: "500", display: "flex", alignItems: "center" }}>
            {pred.name}
            {pred.isNew && (
              <span style={{ 
                fontSize: "10px", 
                backgroundColor: "#d6eaf8", 
                color: "#2874a6", 
                padding: "2px 4px", 
                borderRadius: "3px", 
                marginLeft: "5px" 
              }}>
                New
              </span>
            )}
            {pred.isModified && !pred.isNew && (
              <span style={{ 
                fontSize: "10px", 
                backgroundColor: "#ffeaa7", 
                color: "#d35400", 
                padding: "2px 4px", 
                borderRadius: "3px", 
                marginLeft: "5px" 
              }}>
                Modified
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <div style={{ 
              backgroundColor: pred.confidence > 0.7 ? "#d4edda" : pred.confidence > 0.5 ? "#fff3cd" : "#f8d7da", 
              color: pred.confidence > 0.7 ? "#155724" : pred.confidence > 0.5 ? "#856404" : "#721c24",
              padding: "2px 6px",
              borderRadius: "3px",
              fontSize: "12px",
              fontWeight: "bold",
              marginRight: "8px"
            }}>
              {(pred.confidence * 100).toFixed(1)}%
            </div>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                removeBox(index);
              }}
              style={{
                border: "none",
                background: "none",
                color: "#e74c3c",
                cursor: "pointer",
                padding: "0",
                fontSize: "16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "20px",
                height: "20px",
              }}
              title="Remove this finding"
            >
              ×
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default PredictionItem;