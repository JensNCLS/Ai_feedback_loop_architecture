import FeedbackCommit from "./FeedbackCommit";
import React, { useState, useRef, useEffect } from "react";
import { Rnd } from "react-rnd"; // Import react-rnd

function ImageUpload() {
  const [image, setImage] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [imageUrl, setImageUrl] = useState("");
  const [error, setError] = useState("");
  const [preprocessedImageId, setPreprocessedImageId] = useState(null);
  const [analyzedImageId, setAnalyzedImageId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState("");
  const imgRef = useRef(null);

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
      const response = await fetch("/api/upload/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Backend response:", data);

        setPreprocessedImageId(data.preprocessed_image_id);
        setAnalysisStatus("in_progress");

        setError("");
      } else {
        const errorMessage = `Failed to upload image. Status: ${response.status}`;
        console.error(errorMessage);
        setError(errorMessage);
      }
    } catch (err) {
      console.error("Error during upload:", err);
      setError("An error occurred while uploading the image.");
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
                isModified: false, // Track if the box has been modified
              }))
            );
            setAnalyzedImageId(data.analyzed_image_id);
            setAnalysisStatus("completed");
            clearInterval(intervalId);
          } else {
            setAnalysisStatus("in_progress");
          }
        }
      } catch (error) {
        console.error("Error checking analysis status:", error);
        setError("An error occurred while checking the analysis status.");
        clearInterval(intervalId);
      }
    }, 500);

    return () => clearInterval(intervalId);
  }, [preprocessedImageId]);

  const getScaledImageDimensions = () => {
    const imgElement = imgRef.current;
    if (imgElement) {
      return {
        width: imgElement.clientWidth,
        height: imgElement.clientHeight,
        naturalWidth: imgElement.naturalWidth,
        naturalHeight: imgElement.naturalHeight,
      };
    }
    return { width: 0, height: 0, naturalWidth: 0, naturalHeight: 0 };
  };

  const handleBoxChange = (index, newBox) => {
    setPredictions((prevPredictions) =>
      prevPredictions.map((pred, i) =>
        i === index ? { ...pred, ...newBox, isModified: true } : pred
      )
    );
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
            style={{
              padding: "10px 15px",
              backgroundColor: "#3498db",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Upload
          </button>
        </form>
        {error && <p style={{ color: "red", fontSize: "12px" }}>{error}</p>}
      </div>

      {/* Center: Image Display */}
      <div
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          position: "relative",
        }}
      >
        {imageUrl && (
          <div
            style={{
              position: "relative",
              width: "100%",
              maxWidth: "800px",
            }}
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
              }}
            />
            {predictions.map((pred, index) => {
              const { width, height, naturalWidth, naturalHeight } =
                getScaledImageDimensions();

              const scaleX = width / naturalWidth;
              const scaleY = height / naturalHeight;

              return (
                <Rnd
  key={index}
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
    // Update position while keeping the size consistent
    handleBoxChange(index, {
      xmin: d.x / scaleX,
      ymin: d.y / scaleY,
      xmax: (d.x + (pred.xmax - pred.xmin) * scaleX) / scaleX,
      ymax: (d.y + (pred.ymax - pred.ymin) * scaleY) / scaleY,
    });
  }}
  onResizeStop={(e, direction, ref, delta, position) => {
    // Update size and position after resizing
    handleBoxChange(index, {
      xmin: position.x / scaleX,
      ymin: position.y / scaleY,
      xmax: (position.x + ref.offsetWidth) / scaleX,
      ymax: (position.y + ref.offsetHeight) / scaleY,
    });
  }}
  style={{
    border: "2px solid #e74c3c",
    backgroundColor: "rgba(231, 76, 60, 0.3)",
  }}
>
  <span
    style={{
      position: "absolute",
      top: "-20px",
      left: "0",
      backgroundColor: "#e74c3c",
      color: "white",
      padding: "2px 5px",
      fontSize: "12px",
      borderRadius: "3px",
    }}
  >
    {pred.name} ({(pred.confidence * 100).toFixed(2)}%)
  </span>
</Rnd>
              );
            })}
          </div>
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

export default ImageUpload;