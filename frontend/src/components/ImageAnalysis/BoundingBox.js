import React from 'react';
import { Rnd } from 'react-rnd';

const BoundingBox = ({ 
  pred, 
  index, 
  scaleX, 
  scaleY, 
  isHovered, 
  handleBoxChange, 
  setHoveredItem, 
  removeBox 
}) => {
  return (
    <Rnd
      bounds="parent"
      size={{
        width: (pred.xmax - pred.xmin) * scaleX,
        height: (pred.ymax - pred.ymin) * scaleY,
      }}
      position={{
        x: pred.xmin * scaleX,
        y: pred.ymin * scaleY,
      }}
      onDragStop={(e, d) => {
        handleBoxChange(index, {
          xmin: d.x / scaleX,
          ymin: d.y / scaleY,
          xmax: (d.x + (pred.xmax - pred.xmin) * scaleX) / scaleX,
          ymax: (d.y + (pred.ymax - pred.ymin) * scaleY) / scaleY,
        });
      }}
      onResizeStop={(e, direction, ref, delta, position) => {
        handleBoxChange(index, {
          xmin: position.x / scaleX,
          ymin: position.y / scaleY,
          xmax: (position.x + ref.offsetWidth) / scaleX,
          ymax: (position.y + ref.offsetHeight) / scaleY,
        });
      }}
      enableResizing={{
        top: true,
        right: true,
        bottom: true,
        left: true,
        topRight: true,
        bottomRight: true,
        bottomLeft: true,
        topLeft: true
      }}
      resizeGrid={[1, 1]}
      dragGrid={[1, 1]}
      style={{
        border: `2px solid ${isHovered ? "#2ecc71" : pred.isNew ? "#3498db" : "#e74c3c"}`,
        backgroundColor: isHovered 
          ? "rgba(46, 204, 113, 0.3)"
          : pred.isNew
            ? "rgba(52, 152, 219, 0.3)"
            : "rgba(231, 76, 60, 0.2)",
        zIndex: isHovered ? 20 : 10,
        cursor: "move",
      }}
      onMouseEnter={() => setHoveredItem(index)}
      onMouseLeave={() => setHoveredItem(null)}
      onDoubleClick={() => removeBox(index)}
    />
  );
};

export default BoundingBox;