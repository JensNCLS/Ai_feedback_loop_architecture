import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ImageAnalysis from './components/ImageAnalysis';
import ReviewList from './components/ReviewList';
import ReviewDetail from './components/ReviewList/ReviewDetail';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="app-header">
          <div className="app-title">AI Feedback Loop System</div>
          <div className="app-nav">
            <Link to="/" className="nav-link">Image Analysis</Link>
            <Link to="/review" className="nav-link">Second Review</Link>
          </div>
        </nav>
        
        <div className="app-content">
          <Routes>
            <Route path="/" element={<ImageAnalysis />} />
            <Route path="/review" element={<ReviewList />} />
            <Route path="/review/:id" element={<ReviewDetail />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
