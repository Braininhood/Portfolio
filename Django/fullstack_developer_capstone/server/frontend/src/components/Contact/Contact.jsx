import React, { useState } from 'react';
import './Contact.css';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the form data to your backend
    alert('Thank you for your message! We will get back to you soon.');
    setFormData({ name: '', email: '', subject: '', message: '' });
  };

  return (
    <div className="contact-container">
      <div className="contact-hero">
        <h1>Contact Us</h1>
        <p>Get in touch with our team for support and inquiries</p>
      </div>

      <div className="contact-content">
        <div className="contact-info">
          <h2>📞 Get In Touch</h2>
          <div className="contact-methods">
            <div className="contact-method">
              <h3>🏢 Headquarters</h3>
              <p>123 Dealership Avenue<br />
                 Business District<br />
                 New York, NY 10001</p>
            </div>
            
            <div className="contact-method">
              <h3>📧 Email Support</h3>
              <p>General Inquiries: info@dealership.com<br />
                 Technical Support: support@dealership.com<br />
                 Sales: sales@dealership.com</p>
            </div>
            
            <div className="contact-method">
              <h3>📱 Phone Support</h3>
              <p>Main Line: (555) 123-4567<br />
                 Support: (555) 123-4568<br />
                 Sales: (555) 123-4569</p>
            </div>
            
            <div className="contact-method">
              <h3>🕒 Business Hours</h3>
              <p>Monday - Friday: 9:00 AM - 6:00 PM<br />
                 Saturday: 10:00 AM - 4:00 PM<br />
                 Sunday: Closed</p>
            </div>
          </div>
        </div>

        <div className="contact-form-section">
          <h2>💬 Send Us a Message</h2>
          <form className="contact-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter your full name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="Enter your email address"
              />
            </div>

            <div className="form-group">
              <label htmlFor="subject">Subject *</label>
              <select
                id="subject"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                required
              >
                <option value="">Select a subject</option>
                <option value="general">General Inquiry</option>
                <option value="technical">Technical Support</option>
                <option value="dealer">Dealer Partnership</option>
                <option value="feedback">Feedback</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="message">Message *</label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                required
                rows="6"
                placeholder="Enter your message here..."
              ></textarea>
            </div>

            <button type="submit" className="submit-btn">
              Send Message 📤
            </button>
          </form>
        </div>
      </div>

      <div className="faq-section">
        <h2>❓ Frequently Asked Questions</h2>
        <div className="faq-grid">
          <div className="faq-item">
            <h3>How does the AI sentiment analysis work?</h3>
            <p>Our AI analyzes customer reviews using natural language processing to determine sentiment (positive, negative, neutral) and provides insights to help dealers improve their services.</p>
          </div>
          <div className="faq-item">
            <h3>How can I become a partner dealer?</h3>
            <p>Contact our sales team at sales@dealership.com or call (555) 123-4569 to learn about our dealer partnership program and requirements.</p>
          </div>
          <div className="faq-item">
            <h3>Is the platform available 24/7?</h3>
            <p>Yes, our platform is available 24/7. However, customer support is available during business hours. For urgent technical issues, please email support@dealership.com.</p>
          </div>
          <div className="faq-item">
            <h3>How accurate is the sentiment analysis?</h3>
            <p>Our AI sentiment analysis has a 95% accuracy rate and is continuously improved through machine learning algorithms and user feedback.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact; 