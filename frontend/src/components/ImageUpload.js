import React, { useState, useRef } from 'react';

function ImageUpload() {
  const [image, setImage] = useState(null);
  const [predictions, setPredictions] = useState([]);  // Store predictions here
  const [imageUrl, setImageUrl] = useState('');  // Store image URL here
  const imgRef = useRef(null);  // Reference for the image element

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    setImage(file);
    setImageUrl(URL.createObjectURL(file));  // Create object URL for image preview
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!image) {
      alert("Please select an image");
      return;
    }

    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await fetch('/api/upload/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setPredictions(data.predictions);  // Set the predictions from backend response
      } else {
        alert("Failed to upload image");
      }
    } catch (error) {
      console.error("Error uploading image:", error);
      alert("An error occurred while uploading the image");
    }
  };

  // Get the scaled image dimensions after loading
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

  return (
    <div>
      <h1>Upload an Image</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
        />
        <button type="submit">Upload</button>
      </form>

      {/* Display uploaded image */}
      {imageUrl && (
        <div
          style={{
            position: 'relative',
            display: 'inline-block',
            width: '100%',
            maxWidth: '800px',
            height: 'auto',
          }}
        >
          <img
            ref={imgRef}
            src={imageUrl}
            alt="Uploaded"
            style={{
              width: '100%',
              height: 'auto',
              display: 'block',
            }}
          />

          {/* Overlay bounding boxes */}
          {predictions.map((pred, index) => {
            const { naturalWidth, naturalHeight } = getScaledImageDimensions();

            return (
              <div
                key={index}
                style={{
                  position: 'absolute',
                  left: `${(pred.xmin / naturalWidth) * 100}%`,
                  top: `${(pred.ymin / naturalHeight) * 100}%`,
                  width: `${((pred.xmax - pred.xmin) / naturalWidth) * 100}%`,
                  height: `${((pred.ymax - pred.ymin) / naturalHeight) * 100}%`,
                  border: '2px solid red',
                  color: 'red',
                  fontWeight: 'bold',
                  padding: '5px',
                  backgroundColor: 'rgba(255, 0, 0, 0.5)',
                  pointerEvents: 'none',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                {pred.name} ({(pred.confidence * 100).toFixed(2)}%)
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ImageUpload;
