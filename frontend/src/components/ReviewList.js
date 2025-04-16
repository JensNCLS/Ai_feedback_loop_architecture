import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ReviewList.css';

function ReviewList() {
  const [reviewItems, setReviewItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('pending');
  const [sortBy, setSortBy] = useState('newest');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const pageSize = 8;
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchReviewItems = async () => {
      setLoading(true);
      try {
        // Add filter parameter to the API call
        const filterParam = filter !== 'all' ? `&status=${filter}` : '';
        const response = await fetch(`/api/review-items/?page=${page}&page_size=${pageSize}${filterParam}&sort_by=${sortBy}`);
        
        if (response.ok) {
          const data = await response.json();
          setReviewItems(data.items || []);
          setTotalPages(data.total_pages || 1);
          setTotalItems(data.total_items || 0);
        } else {
          setError('Failed to fetch review items');
        }
      } catch (err) {
        setError('Error fetching review items: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReviewItems();
  }, [page, filter, sortBy]); // Added sortBy as dependency

  const handleReviewClick = (itemId) => {
    navigate(`/review/${itemId}`);
  };

  const handlePageChange = (newPage) => {
    if (newPage > 0 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setPage(1); // Reset to page 1 when changing filters
  };

  const handleSortChange = (event) => {
    setSortBy(event.target.value);
    setPage(1); // Reset to page 1 when changing sort
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="review-list-container">
      <h1>Dermatology Images Flagged for Second Review</h1>
      
      <div className="controls-container">
        <div className="review-filters">
          <span>Filter by status:</span>
          <button 
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => handleFilterChange('pending')}
          >
            Pending
          </button>
          <button 
            className={`filter-btn ${filter === 'reviewed' ? 'active' : ''}`}
            onClick={() => handleFilterChange('reviewed')}
          >
            Reviewed
          </button>
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => handleFilterChange('all')}
          >
            All
          </button>
        </div>

        <div className="sort-controls">
          <label htmlFor="sort-select">Sort by:</label>
          <select 
            id="sort-select" 
            value={sortBy} 
            onChange={handleSortChange}
            className="sort-select"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
          </select>
        </div>
      </div>
      
      {loading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading review items...</p>
        </div>
      )}
      
      {error && <div className="error-message">{error}</div>}
      
      {!loading && !error && reviewItems.length === 0 && (
        <div className="empty-state">
          <p>No items currently flagged for review{filter !== 'all' ? ` with status: ${filter}` : ''}.</p>
        </div>
      )}
      
      {reviewItems.length > 0 && (
        <>
          <div className="review-grid">
            {reviewItems.map(item => (
              <div 
                key={item.id} 
                className="review-card"
                onClick={() => handleReviewClick(item.id)}
              >
                <div className="review-image-container">
                  {/* Using lazy loading for images */}
                  <img 
                    src={item.image_url || '/placeholder-image.jpg'} 
                    alt={`Case ${item.id}`}
                    className="review-thumbnail"
                    loading="lazy"
                  />
                  <span className={`status-badge ${item.status}`}>
                    {item.status}
                  </span>
                </div>
                <div className="review-card-content">
                  <h3>Case #{item.id}</h3>
                  <p className="timestamp">Submitted: {formatDate(item.feedback_given_at)}</p>
                  <p className="review-reason">{item.review_reason}</p>
                  <p className="finding-count">
                    {item.prediction_count || 0} finding{(item.prediction_count !== 1) ? 's' : ''}
                  </p>
                  <button className="review-btn">
                    Review Case
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination controls */}
          <div className="pagination-controls">
            <button 
              onClick={() => handlePageChange(page - 1)} 
              disabled={page === 1}
              className="pagination-btn"
            >
              Previous
            </button>
            <span className="page-indicator">
              Page {page} of {totalPages} ({totalItems} total items)
            </span>
            <button 
              onClick={() => handlePageChange(page + 1)} 
              disabled={page === totalPages}
              className="pagination-btn"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default ReviewList;