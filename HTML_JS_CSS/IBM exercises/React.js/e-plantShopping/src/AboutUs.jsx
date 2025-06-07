import React from 'react';
import './AboutUs.css';

function AboutUs() {
  return (
    <div className="about-us-container">
      <div className="about-us-header">
        <h2 className="about-us-heading">About Us</h2>
        <div className="about-us-divider"></div>
        <p className="about-us-tagline">Where Green Meets Serenity</p>
      </div>

      <div className="about-us-sections">
        <div className="about-us-section">
          <div className="section-content">
            <h3>Our Mission</h3>
            <p>
              At Paradise Nursery, we are dedicated to enhancing lives through the beauty and benefits of plants. 
              Our mission is to provide exceptional quality plants that not only beautify spaces but also contribute 
              to healthier living environments and sustainable ecosystems.
            </p>
          </div>
        </div>

        <div className="about-us-section">
          <div className="section-content">
            <h3>Our Expertise</h3>
            <p>
              With over 15 years of horticultural experience, our team of certified botanists and plant specialists 
              carefully selects and nurtures each plant in our collection. We specialize in air-purifying plants, 
              aromatic varieties, medicinal herbs, insect-repellent species, and low-maintenance options suitable 
              for any environment.
            </p>
          </div>
        </div>

        <div className="about-us-section">
          <div className="section-content">
            <h3>Our Commitment</h3>
            <p>
              We're committed to sustainable practices throughout our operations, from eco-friendly growing methods 
              to biodegradable packaging. Every purchase supports our environmental initiatives, including community 
              garden projects and educational programs on plant care and conservation.
            </p>
          </div>
        </div>
      </div>

      <div className="about-us-footer">
        <p>
          Whether you're an experienced gardener or just beginning your plant journey, our knowledgeable team is here 
          to guide you. Visit Paradise Nursery today to discover the perfect botanical companions for your home, office, 
          or garden.
        </p>
        <div className="about-us-values">
          <span>Quality</span>
          <span>•</span>
          <span>Sustainability</span>
          <span>•</span>
          <span>Expertise</span>
          <span>•</span>
          <span>Service</span>
        </div>
      </div>
    </div>
  );
}

export default AboutUs;
