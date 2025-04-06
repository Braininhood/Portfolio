import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Form, Button } from 'react-bootstrap';
import Comment from './Comment';
import EmojiPicker from './EmojiPicker';

const Comments = ({ postId, isAuthenticated }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch comments when component mounts or postId changes
  useEffect(() => {
    loadComments();
  }, [postId]);

  const loadComments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`/api/posts/${postId}/comments`);
      setComments(response.data.comments);
    } catch (error) {
      console.error('Error loading comments:', error);
      setError('Failed to load comments. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async () => {
    if (newComment.trim() === '' || isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      await axios.post(`/api/posts/${postId}/comments/create`, {
        content: newComment
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      // Reset form and reload comments
      setNewComment('');
      loadComments();
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInsertEmoji = (emoji) => {
    setNewComment(prevComment => prevComment + emoji);
  };

  const handleUpdateComment = (commentId, content) => {
    // Update the comment in the local state
    setComments(prevComments => {
      return prevComments.map(comment => {
        if (comment.id === commentId) {
          return { ...comment, content, is_edited: true };
        }
        
        // Check if the comment is in replies
        if (comment.replies) {
          const updatedReplies = comment.replies.map(reply => {
            if (reply.id === commentId) {
              return { ...reply, content, is_edited: true };
            }
            return reply;
          });
          
          return { ...comment, replies: updatedReplies };
        }
        
        return comment;
      });
    });
  };

  const handleAddReply = (newReply) => {
    // Reload comments to get the updated structure with new reply
    loadComments();
  };

  if (loading) {
    return <div className="text-center my-3">Loading comments...</div>;
  }

  if (error) {
    return <div className="text-center my-3 text-danger">{error}</div>;
  }

  return (
    <div className="comments-section">
      <h5 className="mb-3">Comments</h5>
      
      {isAuthenticated && (
        <Form className="mb-4">
          <Form.Group>
            <Form.Control
              as="textarea"
              rows={3}
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Write a comment..."
              className="comment-textarea"
            />
          </Form.Group>
          <div className="d-flex justify-content-between mt-2">
            <EmojiPicker onEmojiSelect={handleInsertEmoji} />
            <Button 
              variant="primary" 
              onClick={handleSubmitComment}
              disabled={isSubmitting || !newComment.trim()}
            >
              Comment
            </Button>
          </div>
        </Form>
      )}
      
      {comments.length === 0 ? (
        <div className="text-center my-3">No comments yet. Be the first to comment!</div>
      ) : (
        <div>
          {comments.map(comment => (
            <Comment
              key={comment.id}
              comment={comment}
              postId={postId}
              onUpdateComment={handleUpdateComment}
              onAddReply={handleAddReply}
              isAuthenticated={isAuthenticated}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Comments; 