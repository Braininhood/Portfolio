import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button } from 'react-bootstrap';
import EmojiPicker from './EmojiPicker';

const NewPost = ({ onPostCreated }) => {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (content.trim() === '') {
      setError('Post content cannot be empty');
      return;
    }
    
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    setError('');
    
    try {
      await axios.post('/api/posts/create', {
        content
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      setContent('');
      onPostCreated();
    } catch (error) {
      console.error('Error creating post:', error);
      setError('Failed to create post. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInsertEmoji = (emoji) => {
    setContent(prevContent => prevContent + emoji);
  };

  return (
    <div className="new-post-form">
      <h5>New Post</h5>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Form.Control
            as="textarea"
            rows={3}
            placeholder="What's happening?"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="new-post-textarea"
            maxLength={280}
          />
        </Form.Group>
        
        {error && <p className="text-danger">{error}</p>}
        
        <div className="d-flex justify-content-between align-items-center mt-2">
          <div className="d-flex align-items-center">
            <EmojiPicker onEmojiSelect={handleInsertEmoji} />
            <small className="text-muted ms-2">{content.length}/280</small>
          </div>
          <Button 
            type="submit" 
            variant="primary" 
            className="new-post-button"
            disabled={isSubmitting || content.trim() === ''}
          >
            {isSubmitting ? 'Posting...' : 'Post'}
          </Button>
        </div>
      </Form>
    </div>
  );
};

export default NewPost; 