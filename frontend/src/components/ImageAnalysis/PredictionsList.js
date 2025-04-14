import React from 'react';
import PredictionItem from './PredictionItem';

const PredictionsList = ({
  predictions,
  editingItem,
  hoveredItem,
  tempName,
  setTempName,
  tempConfidence,
  setTempConfidence,
  saveEditing,
  removeBox,
  startEditing,
  setEditingItem,
  setHoveredItem
}) => {
  if (predictions.length === 0) return null;

  return (
    <div style={{ width: "100%", marginTop: "20px" }}>
      <h3 style={{ fontSize: "16px", marginBottom: "10px", textAlign: "center" }}>
        Detected Items
      </h3>
      <div 
        style={{ 
          maxHeight: "300px", 
          overflowY: "auto",
          border: "1px solid #e0e0e0",
          borderRadius: "5px",
          padding: "10px"
        }}
      >
        {predictions.map((pred, index) => (
          <PredictionItem 
            key={index}
            pred={pred}
            index={index}
            isEditing={editingItem === index}
            isHovered={hoveredItem === index}
            tempName={tempName}
            setTempName={setTempName}
            tempConfidence={tempConfidence}
            setTempConfidence={setTempConfidence}
            saveEditing={saveEditing}
            cancelEditing={() => setEditingItem(null)}
            removeBox={removeBox}
            startEditing={startEditing}
            handleHover={setHoveredItem}
          />
        ))}
      </div>
    </div>
  );
};

export default PredictionsList;