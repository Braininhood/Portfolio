import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>🚗 Welcome to Dealership Management System</h1>
        <p>Your comprehensive solution for car dealership management with AI-powered insights</p>
        <div className="cta-buttons">
          <Link to="/dealers" className="btn btn-primary">Browse Dealers</Link>
          <Link to="/login" className="btn btn-secondary">Login</Link>
          <Link to="/register" className="btn btn-tertiary">Register</Link>
        </div>
      </div>
      
      <div className="ai-highlight-section">
        <div className="ai-banner">
          <h2>🤖 AI-Powered Sentiment Analysis</h2>
          <p>Experience the future of customer feedback analysis with our advanced AI technology</p>
        </div>
        <div className="ai-features">
          <div className="ai-feature">
            <div className="sentiment-positive">😊</div>
            <h3>Positive Reviews</h3>
            <p>Automatically detect and highlight positive customer experiences</p>
          </div>
          <div className="ai-feature">
            <div className="sentiment-neutral">😐</div>
            <h3>Neutral Feedback</h3>
            <p>Identify areas for improvement with neutral sentiment analysis</p>
          </div>
          <div className="ai-feature">
            <div className="sentiment-negative">😞</div>
            <h3>Negative Concerns</h3>
            <p>Quickly address customer concerns with negative sentiment detection</p>
          </div>
        </div>
      </div>
      
      <div className="features-section">
        <h2>Platform Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <h3>🏪 Dealer Management</h3>
            <p>Browse and manage dealerships across multiple states with comprehensive dealer profiles</p>
            <Link to="/dealers" className="feature-link">View Dealers →</Link>
          </div>
          <div className="feature-card highlight-ai">
            <h3>🧠 AI Review Analysis</h3>
            <p>Customer reviews with AI-powered sentiment analysis providing real-time insights</p>
            <div className="ai-stats">
              <span className="stat">95% Accuracy</span>
              <span className="stat">Real-time Processing</span>
            </div>
          </div>
          <div className="feature-card">
            <h3>🚗 Car Database</h3>
            <p>Comprehensive car inventory management with detailed specifications and pricing</p>
          </div>
          <div className="feature-card">
            <h3>🔐 Secure Authentication</h3>
            <p>Advanced user authentication and authorization system for secure access</p>
            <Link to="/register" className="feature-link">Get Started →</Link>
          </div>
          <div className="feature-card">
            <h3>📊 Analytics Dashboard</h3>
            <p>Real-time analytics and reporting with sentiment trends and performance metrics</p>
          </div>
          <div className="feature-card">
            <h3>🌐 Multi-Platform</h3>
            <p>Access from anywhere with our responsive web application and API integration</p>
          </div>
        </div>
      </div>

      <div className="demo-section">
        <h2>See AI Sentiment Analysis in Action</h2>
        <div className="demo-reviews">
          <div className="demo-review positive">
            <div className="review-text">"Excellent service and great car selection!"</div>
            <div className="sentiment-result">
              <span className="sentiment-label positive">AI Analysis: Positive 😊</span>
              <span className="confidence">Confidence: 96%</span>
            </div>
          </div>
          <div className="demo-review negative">
            <div className="review-text">"Poor customer service, very disappointed."</div>
            <div className="sentiment-result">
              <span className="sentiment-label negative">AI Analysis: Negative 😞</span>
              <span className="confidence">Confidence: 94%</span>
            </div>
          </div>
          <div className="demo-review neutral">
            <div className="review-text">"The car is okay, nothing special."</div>
            <div className="sentiment-result">
              <span className="sentiment-label neutral">AI Analysis: Neutral 😐</span>
              <span className="confidence">Confidence: 89%</span>
            </div>
          </div>
        </div>
        <div className="demo-cta">
          <Link to="/dealers" className="btn btn-primary">Try It Now - Browse Dealers</Link>
        </div>
      </div>
    </div>
  );
};

export default Home; 