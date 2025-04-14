import React from 'react';

const ImageUploader = ({ handleImageChange, handleSubmit, error, loading }) => {
  return (
    <div>
      <h2 style={{ fontSize: "20px", marginBottom: "20px" }}>Upload Image</h2>
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{
            marginBottom: "10px",
            padding: "10px",
            borderRadius: "5px",
            border: "1px solid #bdc3c7",
            width: "100%",
            maxWidth: "200px",
            fontSize: "14px",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "10px 15px",
            backgroundColor: "#3498db",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "14px",
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
    </div>
  );
};

export default ImageUploader;