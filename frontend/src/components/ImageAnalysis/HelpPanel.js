import React from 'react';

const HelpPanel = ({ showHelp, setShowHelp }) => {
  return (
    <div style={{ marginTop: "20px", width: "100%", textAlign: "center" }}>
      <button
        onClick={() => setShowHelp(!showHelp)}
        style={{
          padding: "8px 15px",
          backgroundColor: "#7f8c8d",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          fontSize: "13px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto",
        }}
      >
        <span style={{ marginRight: "5px" }}>
          {showHelp ? "Hide Help" : "Show Help"}
        </span>
        {showHelp ? "▲" : "▼"}
      </button>
      
      {showHelp && (
        <div style={{ 
          marginTop: "10px", 
          textAlign: "left", 
          fontSize: "13px", 
          color: "#7f8c8d",
          padding: "10px",
          backgroundColor: "#f8f9fa",
          borderRadius: "5px",
          border: "1px solid #e0e0e0" 
        }}>
          <p style={{ margin: "5px 0", fontWeight: "bold" }}>
            Drawing Tools:
          </p>
          <p style={{ margin: "5px 0" }}>
            • Click and drag on image to draw a new box
          </p>
          <p style={{ margin: "5px 0" }}>
            • Double-click on a box to remove it
          </p>
          <p style={{ margin: "5px 0" }}>
            • Drag or resize boxes to adjust them
          </p>
          <p style={{ margin: "5px 0" }}>
            • Click × in the sidebar to remove a finding
          </p>
        </div>
      )}
    </div>
  );
};

export default HelpPanel;