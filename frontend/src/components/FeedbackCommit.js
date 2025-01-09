import React, { useState } from 'react';

function FeedbackCommit({ labeledImage, predictions }) {
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Handle feedback submission
  const handleFeedbackSubmit = async () => {
    if (!labeledImage || predictions.length === 0) {
      setError('No labeled image or predictions available.');
      return;
    }

    const formData = new FormData();
formData.append('labeled_image', labeledImage);
formData.append('predictions', JSON.stringify(predictions));
if (feedback) {
  formData.append('feedback', feedback);
}


    try {
      const response = await fetch('/api/feedback/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        setSuccess('Feedback successfully submitted!');
        setError('');
      } else {
        const errorMessage = `Failed to submit feedback. Status: ${response.status}`;
        console.error(errorMessage);
        setError(errorMessage);
        setSuccess('');
      }
    } catch (err) {
      console.error('Error during feedback submission:', err);
      setError('An error occurred while submitting feedback.');
      setSuccess('');
    }
  };

  return (
    <div
      style={{
        padding: '20px',
        backgroundColor: '#ecf0f1',
        borderRadius: '10px',
        boxShadow: '0 0 10px rgba(0, 0, 0, 0.1)',
        marginTop: '20px',
      }}
    >
      <h2 style={{ fontSize: '20px', marginBottom: '10px' }}>Submit Feedback</h2>

      {/* Feedback text area */}
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Add your feedback about the predictions (optional)..."
        style={{
          width: '100%',
          height: '80px',
          padding: '10px',
          borderRadius: '5px',
          border: '1px solid #bdc3c7',
          marginBottom: '10px',
        }}
      ></textarea>

      {/* Submit Button */}
      <button
        onClick={handleFeedbackSubmit}
        style={{
          padding: '10px 15px',
          backgroundColor: '#27ae60',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          fontSize: '16px',
        }}
      >
        Submit Feedback
      </button>

      {/* Success/Error Messages */}
      {success && <p style={{ color: 'green', marginTop: '10px' }}>{success}</p>}
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
    </div>
  );
}

export default FeedbackCommit;
