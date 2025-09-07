import React, { createContext, useState, useEffect, useContext, useRef, useCallback } from 'react';
import { authAPI } from '../services/api';

// Create context for authentication
const AuthContext = createContext();

// Auto-signout timeout in milliseconds (2 minutes)
const AUTO_SIGNOUT_TIMEOUT = 2 * 60 * 1000;
const WARNING_BEFORE_SIGNOUT = 30 * 1000; // Show warning 30 seconds before signing out

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Timer for auto-signout
  const autoSignoutTimerRef = useRef(null);
  const warningTimerRef = useRef(null);
  // eslint-disable-next-line no-unused-vars
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showSignoutWarning, setShowSignoutWarning] = useState(false);

  // Define logout function with useCallback to avoid dependency changes
  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('masterKeyStatus');
    setUser(null);
  }, []);
  
  // Reset the auto-signout timer when there's user activity
  const resetAutoSignoutTimer = useCallback(() => {
    setLastActivity(Date.now());
    setShowSignoutWarning(false);
    
    // Clear both timers
    if (autoSignoutTimerRef.current) {
      clearTimeout(autoSignoutTimerRef.current);
      autoSignoutTimerRef.current = null;
    }
    
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    
    if (user) {
      // Set timer for warning
      warningTimerRef.current = setTimeout(() => {
        setShowSignoutWarning(true);
      }, AUTO_SIGNOUT_TIMEOUT - WARNING_BEFORE_SIGNOUT);
      
      // Set timer for auto-signout
      autoSignoutTimerRef.current = setTimeout(() => {
        console.log('Auto-signing out due to inactivity');
        logout();
        setShowSignoutWarning(false);
      }, AUTO_SIGNOUT_TIMEOUT);
    }
  }, [user, logout]);
  
  // Reset the timer when user continues the session
  const continueAuthSession = useCallback(() => {
    resetAutoSignoutTimer();
  }, [resetAutoSignoutTimer]);
  
  // Monitor for user activity
  useEffect(() => {
    const handleActivity = () => {
      resetAutoSignoutTimer();
    };
    
    // Track user activity
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);
    window.addEventListener('scroll', handleActivity);
    
    // Set initial timer
    resetAutoSignoutTimer();
    
    return () => {
      // Clean up event listeners
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('scroll', handleActivity);
      
      // Clear timer on unmount
      if (autoSignoutTimerRef.current) {
        clearTimeout(autoSignoutTimerRef.current);
      }
    };
  }, [user, resetAutoSignoutTimer]);
  
  // Initialize user from localStorage on load
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);
  
  // Register new user
  const register = async (username, email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authAPI.register(username, email, password);
      const userData = response.data;
      
      // Store token and user data
      localStorage.setItem('token', userData.token);
      localStorage.setItem('user', JSON.stringify({
        id: userData.user_id,
        username: userData.username,
        email: userData.email
      }));
      
      setUser({
        id: userData.user_id,
        username: userData.username,
        email: userData.email
      });
      
      return userData;
    } catch (err) {
      setError(err.response?.data?.error || JSON.stringify(err.response?.data) || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Login user
  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authAPI.login(username, password);
      const userData = response.data;
      
      // Store token and user data
      localStorage.setItem('token', userData.token);
      localStorage.setItem('user', JSON.stringify({
        id: userData.user_id,
        username: userData.username,
        email: userData.email
      }));
      
      setUser({
        id: userData.user_id,
        username: userData.username,
        email: userData.email
      });
      
      return userData;
    } catch (err) {
      setError(err.response?.data?.error || JSON.stringify(err.response?.data) || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Check if user is authenticated
  const isAuthenticated = () => {
    return !!user && !!localStorage.getItem('token');
  };
  
  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        register,
        login,
        logout,
        isAuthenticated,
        showSignoutWarning,
        continueAuthSession
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 