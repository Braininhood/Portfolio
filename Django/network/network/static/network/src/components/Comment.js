import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button } from 'react-bootstrap';
import EmojiPicker from './EmojiPicker';
import EmojiReaction from './EmojiReaction';

const Comment = ({ comment, postId, onUpdateComment, onAddReply, isAuthenticated }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isReplying, setIsReplying] = useState(false);
  const [content, setContent] = useState(comment.content);
  const [replyContent, setReplyContent] = useState('');
  const [reactions, setReactions] = useState(comment.reactions || {});
  const [userReactions, setUserReactions] = useState(comment.user_reactions || []);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (content.trim() === '' || isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      await axios.put(`/api/comments/${comment.id}/edit`, {
        content
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      onUpdateComment(comment.id, content);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setContent(comment.content);
    setIsEditing(false);
  };

  const handleReply = () => {
    setIsReplying(true);
  };

  const handleSubmitReply = async () => {
    if (replyContent.trim() === '' || isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      const response = await axios.post(`/api/posts/${postId}/comments/create`, {
        content: replyContent,
        parent_id: comment.id
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      onAddReply(response.data);
      setReplyContent('');
      setIsReplying(false);
    } catch (error) {
      console.error('Error adding reply:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelReply = () => {
    setReplyContent('');
    setIsReplying(false);
  };

  const handleInsertEmoji = (emoji) => {
    setContent(prevContent => prevContent + emoji);
  };

  const handleInsertReplyEmoji = (emoji) => {
    setReplyContent(prevContent => prevContent + emoji);
  };

  const handleReaction = async (emoji) => {
    if (!isAuthenticated) return;

    try {
      const response = await axios.post(`/api/comments/${comment.id}/reaction`, { 
        emoji 
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      setReactions(response.data.reactions);
      setUserReactions(response.data.user_reactions);
    } catch (error) {
      console.error('Error adding reaction:', error);
    }
  };

  return (
    <div className="comment mb-3">
      <div className="d-flex justify-content-between">
        <div>
          <span className="fw-bold">{comment.user}</span>
          <span className="ms-2 text-muted small">{comment.timestamp}</span>
          {comment.is_edited && <span className="text-muted small ms-1">(edited)</span>}
        </div>
        <div>
          {comment.is_owner && !isEditing && (
            <button className="edit-comment-btn" onClick={handleEdit}>
              <i className="fas fa-edit"></i> Edit
            </button>
          )}
          {isAuthenticated && !isEditing && !isReplying && (
            <button className="reply-btn ms-2" onClick={handleReply}>
              <i className="fas fa-reply"></i> Reply
            </button>
          )}
        </div>
      </div>
      
      {!isEditing ? (
        <div className="comment-content mt-1">{comment.content}</div>
      ) : (
        <Form className="mt-3">
          <Form.Group>
            <Form.Control
              as="textarea"
              rows={2}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="comment-edit-textarea"
            />
          </Form.Group>
          <div className="d-flex justify-content-between mt-2">
            <EmojiPicker onEmojiSelect={handleInsertEmoji} />
            <div className="d-flex gap-2">
              <Button variant="secondary" size="sm" onClick={handleCancel} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSave} disabled={isSubmitting}>
                Save
              </Button>
            </div>
          </div>
        </Form>
      )}
      
      {isReplying && (
        <Form className="mt-3">
          <Form.Group>
            <Form.Control
              as="textarea"
              rows={2}
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="Write a reply..."
              className="reply-textarea"
            />
          </Form.Group>
          <div className="d-flex justify-content-between mt-2">
            <EmojiPicker onEmojiSelect={handleInsertReplyEmoji} />
            <div className="d-flex gap-2">
              <Button variant="secondary" size="sm" onClick={handleCancelReply} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSubmitReply} disabled={isSubmitting}>
                Reply
              </Button>
            </div>
          </div>
        </Form>
      )}
      
      {comment.replies && comment.replies.length > 0 && (
        <div className="replies ms-4 mt-3">
          {comment.replies.map(reply => (
            <Comment
              key={reply.id}
              comment={reply}
              postId={postId}
              onUpdateComment={onUpdateComment}
              onAddReply={onAddReply}
              isAuthenticated={isAuthenticated}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Comment; 