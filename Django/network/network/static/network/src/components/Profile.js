import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { Container, Button, Alert, Card } from 'react-bootstrap';
import Post from './Post';
import Pagination from './Pagination';

const Profile = ({ user, isAuthenticated }) => {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFollowing, setIsFollowing] = useState(false);
  const [followersCount, setFollowersCount] = useState(0);

  const fetchProfile = async (pageNum = 1) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`/api/users/${username}?page=${pageNum}`);
      setProfile({
        username: response.data.username,
        followers_count: response.data.followers_count,
        following_count: response.data.following_count
      });
      setPosts(response.data.posts);
      setPage(response.data.page);
      setIsFollowing(response.data.is_following);
      setFollowersCount(response.data.followers_count);
    } catch (error) {
      console.error('Error fetching profile:', error);
      setError('Failed to load profile. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile(currentPage);
  }, [username, currentPage]);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0);
  };

  const handleToggleFollow = async () => {
    if (!isAuthenticated) return;
    
    try {
      const response = await axios.post(`/api/users/${username}/follow`, {}, {
        headers: {
          'X-CSRFToken': window.csrfToken
        }
      });
      
      setIsFollowing(response.data.following);
      setFollowersCount(response.data.followers_count);
    } catch (error) {
      console.error('Error toggling follow:', error);
    }
  };

  const updatePost = (postId, newContent) => {
    setPosts(prevPosts =>
      prevPosts.map(post =>
        post.id === postId ? { ...post, content: newContent } : post
      )
    );
  };

  if (loading && !profile) {
    return <div className="text-center my-5">Loading profile...</div>;
  }

  if (error && !profile) {
    return (
      <Alert variant="danger" className="my-5">
        {error}
      </Alert>
    );
  }

  return (
    <Container>
      {profile && (
        <>
          <Card className="profile-header">
            <Card.Body>
              <h2 className="profile-username">@{profile.username}</h2>
              
              <div className="profile-stats">
                <div>
                  <strong>{followersCount}</strong> {followersCount === 1 ? 'follower' : 'followers'}
                </div>
                <div>
                  <strong>{profile.following_count}</strong> following
                </div>
              </div>
              
              {isAuthenticated && user?.username !== profile.username && (
                <Button
                  variant={isFollowing ? "outline-primary" : "primary"}
                  className="follow-button"
                  onClick={handleToggleFollow}
                >
                  {isFollowing ? "Unfollow" : "Follow"}
                </Button>
              )}
            </Card.Body>
          </Card>

          <h3 className="mb-3">Posts</h3>
          
          {loading ? (
            <div className="text-center my-5">Loading posts...</div>
          ) : (
            <>
              {posts.length === 0 ? (
                <p className="text-center my-5">No posts yet.</p>
              ) : (
                <>
                  {posts.map(post => (
                    <Post
                      key={post.id}
                      post={post}
                      updatePost={updatePost}
                      isAuthenticated={isAuthenticated}
                    />
                  ))}
                  
                  <Pagination
                    page={page}
                    onPageChange={handlePageChange}
                  />
                </>
              )}
            </>
          )}
        </>
      )}
    </Container>
  );
};

export default Profile; 