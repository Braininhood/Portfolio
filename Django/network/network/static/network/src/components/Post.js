import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Card, Button, Form } from 'react-bootstrap';
import EmojiPicker from './EmojiPicker';
import EmojiReaction from './EmojiReaction';
import Comments from './Comments';

const Post = ({ post, updatePost, isAuthenticated }) => {
  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState(post.content);
  const [likesCount, setLikesCount] = useState(post.likes_count);
  const [liked, setLiked] = useState(post.liked_by_user);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reactions, setReactions] = useState(post.reactions || {});
  const [userReactions, setUserReactions] = useState(post.user_reactions || []);
  const [showComments, setShowComments] = useState(false);
  const [commentsCount, setCommentsCount] = useState(post.comments_count || 0);

  const handleLike = async () => {
    if (!isAuthenticated) return;

    try {
      const response = await axios.post(`/api/posts/${post.id}/like`, {}, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      setLikesCount(response.data.likes_count);
      setLiked(response.data.liked);
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const handleEdit = () => {
    setEditing(true);
  };

  const handleSave = async () => {
    if (content.trim() === '' || isSubmitting) return;
    
    setIsSubmitting(true);
    
    try {
      await axios.put(`/api/posts/${post.id}/edit`, {
        content
      }, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      updatePost(post.id, content);
      setEditing(false);
    } catch (error) {
      console.error('Error updating post:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setContent(post.content);
    setEditing(false);
  };

  const handleInsertEmoji = (emoji) => {
    setContent(prevContent => prevContent + emoji);
  };

  const handleReaction = async (emoji) => {
    if (!isAuthenticated) return;

    try {
      const response = await axios.post(`/api/posts/${post.id}/reaction`, { 
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

  const toggleComments = () => {
    setShowComments(!showComments);
  };

  return (
    <Card className="post-card">
      <Card.Body>
        <div className="d-flex justify-content-between">
          <Link to={`/profile/${post.user}`} className="post-username">
            {post.user}
          </Link>
          <span className="post-timestamp">{post.timestamp}</span>
        </div>
        
        {editing ? (
          <Form>
            <Form.Group>
              <Form.Control
                as="textarea"
                rows={3}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="mt-2"
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
        ) : (
          <>
            <p className="post-content">{content}</p>
            
            {/* Emoji reactions display */}
            {Object.keys(reactions).length > 0 && (
              <div className="emoji-reactions">
                {Object.entries(reactions).map(([emoji, count]) => (
                  <EmojiReaction 
                    key={emoji}
                    emoji={emoji}
                    count={count}
                    active={userReactions.includes(emoji)}
                    onClick={() => handleReaction(emoji)}
                  />
                ))}
              </div>
            )}
          </>
        )}
        
        <div className="d-flex mt-3">
          <button 
            className={`like-button ${liked ? 'active' : ''}`} 
            onClick={handleLike}
            disabled={!isAuthenticated}
          >
            <i className={`fa${liked ? 's' : 'r'} fa-heart`}></i> {likesCount}
          </button>
          
          <button 
            className="comment-button ms-3" 
            onClick={toggleComments}
          >
            <i className="far fa-comment"></i> {commentsCount}
          </button>
          
          {isAuthenticated && !editing && (
            <EmojiPicker 
              onEmojiSelect={handleReaction} 
              buttonText="😀"
            />
          )}
          
          {post.is_owner && !editing && (
            <button className="edit-button ms-3" onClick={handleEdit}>
              <i className="fas fa-edit"></i> Edit
            </button>
          )}
        </div>
        
        {showComments && (
          <div className="mt-3">
            <Comments postId={post.id} isAuthenticated={isAuthenticated} />
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default Post; 