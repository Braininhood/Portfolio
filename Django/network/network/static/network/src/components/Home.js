import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Alert } from 'react-bootstrap';
import Post from './Post';
import NewPost from './NewPost';
import Pagination from './Pagination';

const Home = ({ user, isAuthenticated }) => {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPosts = async (pageNum = 1) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`/api/posts?page=${pageNum}`);
      setPosts(response.data.posts);
      setPage(response.data.page);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setError('Failed to load posts. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts(currentPage);
  }, [currentPage]);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0);
  };

  const handlePostCreated = () => {
    // Refresh posts after creating a new one
    setCurrentPage(1);
    fetchPosts(1);
  };

  const updatePost = (postId, newContent) => {
    setPosts(prevPosts =>
      prevPosts.map(post =>
        post.id === postId ? { ...post, content: newContent } : post
      )
    );
  };

  return (
    <Container>
      <h2 className="mb-3">All Posts</h2>
      
      {isAuthenticated && (
        <NewPost onPostCreated={handlePostCreated} />
      )}
      
      {error && (
        <Alert variant="danger" className="mb-3">
          {error}
        </Alert>
      )}
      
      {loading ? (
        <div className="text-center my-5">Loading posts...</div>
      ) : (
        <>
          {posts.length === 0 ? (
            <p>No posts yet. Be the first to post!</p>
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
    </Container>
  );
};

export default Home; 