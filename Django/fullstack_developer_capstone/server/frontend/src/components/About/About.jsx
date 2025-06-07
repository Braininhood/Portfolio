import React from 'react';
import './About.css';

const About = () => {
  return (
    <div className="about-container">
      <div className="about-hero">
        <h1>About Our Dealership Management System</h1>
        <p>Revolutionizing the automotive industry with cutting-edge technology</p>
      </div>
      
      <div className="about-content">
        <div className="about-section">
          <h2>🚗 Our Mission</h2>
          <p>
            We provide a comprehensive dealership management platform that connects 
            customers with trusted car dealers across the nation. Our system streamlines 
            the car buying experience through innovative technology and data-driven insights.
          </p>
        </div>

        <div className="about-section">
          <h2>🤖 AI-Powered Features</h2>
          <div className="features-list">
            <div className="feature-item">
              <h3>Sentiment Analysis</h3>
              <p>Our advanced AI analyzes customer reviews to provide real-time sentiment insights, helping dealers improve their services.</p>
            </div>
            <div className="feature-item">
              <h3>Smart Recommendations</h3>
              <p>Machine learning algorithms suggest the best dealers and vehicles based on customer preferences and reviews.</p>
            </div>
            <div className="feature-item">
              <h3>Automated Insights</h3>
              <p>Get automated reports on dealer performance, customer satisfaction, and market trends.</p>
            </div>
          </div>
        </div>

        <div className="about-section">
          <h2>📊 Platform Statistics</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>50+</h3>
              <p>Verified Dealers</p>
            </div>
            <div className="stat-card">
              <h3>1000+</h3>
              <p>Customer Reviews</p>
            </div>
            <div className="stat-card">
              <h3>95%</h3>
              <p>Accuracy Rate</p>
            </div>
            <div className="stat-card">
              <h3>24/7</h3>
              <p>System Availability</p>
            </div>
          </div>
        </div>

        <div className="about-section">
          <h2>🔧 Technology Stack</h2>
          <div className="tech-stack">
            <div className="tech-category">
              <h3>Frontend</h3>
              <ul>
                <li>React.js</li>
                <li>Bootstrap</li>
                <li>Responsive Design</li>
              </ul>
            </div>
            <div className="tech-category">
              <h3>Backend</h3>
              <ul>
                <li>Django REST Framework</li>
                <li>Node.js Microservices</li>
                <li>PostgreSQL Database</li>
              </ul>
            </div>
            <div className="tech-category">
              <h3>AI/ML</h3>
              <ul>
                <li>Natural Language Processing</li>
                <li>Sentiment Analysis API</li>
                <li>Machine Learning Models</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About; 