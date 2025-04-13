import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Alert } from 'react-bootstrap';
import Post from './Post';
import Pagination from './Pagination';

const Following = ({ user }) => {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFollowingPosts = async (pageNum = 1) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`/api/posts/following?page=${pageNum}`);
      setPosts(response.data.posts);
      setPage(response.data.page);
    } catch (error) {
      console.error('Error fetching following posts:', error);
      setError('Failed to load posts. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFollowingPosts(currentPage);
  }, [currentPage]);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo(0, 0);
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
      <h2 className="mb-4">Following</h2>
      
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
            <div className="text-center my-5">
              <p>No posts to show. Follow more users to see their posts here!</p>
            </div>
          ) : (
            <>
              {posts.map(post => (
                <Post
                  key={post.id}
                  post={post}
                  updatePost={updatePost}
                  isAuthenticated={true}
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

export default Following; 