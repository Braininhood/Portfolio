import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// Import components
import Home from './components/Home';
import Profile from './components/Profile';
import Following from './components/Following';
import Navigation from './components/Navigation';

function App() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // We'll use Django's authenticated user in the template
        // If user is logged in, we should have a username in the global variable
        if (window.user && window.user.username) {
          setUser(window.user);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
    return <div className="text-center my-5">Loading...</div>;
  }

  return (
    <Router>
      <div className="App">
        <Navigation user={user} isAuthenticated={isAuthenticated} />
        <div className="container mt-4">
          <Routes>
            <Route path="/" element={<Home user={user} isAuthenticated={isAuthenticated} />} />
            <Route 
              path="/following" 
              element={
                isAuthenticated ? 
                <Following user={user} /> : 
                <Navigate to="/login" replace />
              } 
            />
            <Route path="/profile/:username" element={<Profile user={user} isAuthenticated={isAuthenticated} />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App; 