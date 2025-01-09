import FeedbackCommit from "./FeedbackCommit";
import React, { useState, useRef, useEffect } from 'react';

function ImageUpload() {
  const [image, setImage] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [imageUrl, setImageUrl] = useState('');
  const [error, setError] = useState('');
  const [preprocessedImageId, setPreprocessedImageId] = useState(null);
  const [analyzedImageId, setAnalyzedImageId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState('');
  const imgRef = useRef(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setImageUrl(URL.createObjectURL(file));
      setPredictions([]);
      setError('');
      setPreprocessedImageId(null);
      setAnalysisStatus('');
      setAnalyzedImageId(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!image) {
      setError('Please select an image to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('image', image);

    try {
      const response = await fetch('/api/upload/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Backend response:', data);

        setPreprocessedImageId(data.preprocessed_image_id);
        setAnalysisStatus('in_progress');

        setError('');
      } else {
        const errorMessage = `Failed to upload image. Status: ${response.status}`;
        console.error(errorMessage);
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error during upload:', err);
      setError('An error occurred while uploading the image.');
    }
  };

  useEffect(() => {
    if (!preprocessedImageId) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`/api/check_analysis_status/${preprocessedImageId}/`);
        const data = await response.json();

        if (data.success) {
          if (data.status === 'completed') {
            setPredictions(data.analysis_results || []);
            setAnalyzedImageId(data.analyzed_image_id);
            setAnalysisStatus('completed');
            clearInterval(intervalId);
          } else {
            setAnalysisStatus('in_progress');
          }
        }
      } catch (error) {
        console.error('Error checking analysis status:', error);
        setError('An error occurred while checking the analysis status.');
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

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Arial, sans-serif' }}>
      <div
        style={{
          width: '300px',
          backgroundColor: '#2c3e50',
          color: 'white',
          padding: '20px',
          overflowY: 'auto',
          boxShadow: '2px 0 5px rgba(0, 0, 0, 0.1)',
          borderRight: '2px solid #34495e',
        }}
      >
        <h1 style={{ fontSize: '24px', marginBottom: '20px' }}>Upload an Image</h1>
        <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            style={{
              marginBottom: '10px',
              padding: '10px',
              borderRadius: '5px',
              border: '1px solid #bdc3c7',
              width: '100%',
              fontSize: '16px',
            }}
          />
          <div>
            <button
              type="submit"
              style={{
                padding: '10px 15px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                width: '100%',
                fontSize: '16px',
                marginTop: '10px',
              }}
            >
              Upload
            </button>
          </div>
        </form>

        {error && <p style={{ color: 'red', fontSize: '14px' }}>{error}</p>}

        {imageUrl && predictions.length > 0 ? (
          <div style={{ marginTop: '20px' }}>
            <h2 style={{ fontSize: '20px', marginBottom: '10px' }}>Predictions:</h2>
            <ul style={{ paddingLeft: '20px' }}>
              {predictions.map((pred, index) => (
                <li key={index} style={{ fontSize: '16px', marginBottom: '8px' }}>
                  {pred.name}: {(pred.confidence * 100).toFixed(2)}%
                </li>
              ))}
            </ul>
          </div>
        ) : (
          imageUrl && <p style={{ color: '#95a5a6' }}>No predictions available.</p>
        )}
      </div>

      <div
        style={{
          flex: 1,
          padding: '20px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: '#ecf0f1',
        }}
      >
        {imageUrl && (
          <div
            style={{
              position: 'relative',
              display: 'inline-block',
              width: '100%',
              maxWidth: '1100px',
              height: 'auto',
              border: '2px solid #bdc3c7',
              borderRadius: '10px',
              backgroundColor: 'white',
              boxShadow: '0 0 10px rgba(0, 0, 0, 0.1)',
              padding: '10px',
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
                borderRadius: '10px',
              }}
            />

            {predictions.length > 0 &&
              predictions.map((pred, index) => {
                const { width, height, naturalWidth, naturalHeight } =
                  getScaledImageDimensions();

                const scaleX = width / naturalWidth;
                const scaleY = height / naturalHeight;

                return (
                  <div
                    key={index}
                    style={{
                      position: 'absolute',
                      left: `${pred.xmin * scaleX}px`,
                      top: `${pred.ymin * scaleY}px`,
                      width: `${(pred.xmax - pred.xmin) * scaleX}px`,
                      height: `${(pred.ymax - pred.ymin) * scaleY}px`,
                      border: '2px solid #e74c3c',
                      backgroundColor: 'rgba(231, 76, 60, 0.5)',
                      pointerEvents: 'none',
                    }}
                  >
                    <span
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        color: 'white',
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        padding: '2px 4px',
                        fontSize: '12px',
                      }}
                    >
                      {pred.name} ({(pred.confidence * 100).toFixed(2)}%)
                    </span>
                  </div>
                );
              })}
          </div>
        )}
      </div>
      {analysisStatus === 'completed' && predictions.length > 0 && (
          <FeedbackCommit
            predictions={predictions}
            preprocessedImageId={preprocessedImageId}
            analyzedImageId={analyzedImageId}
          />
        )}
    </div>
  );
}

export default ImageUpload;
