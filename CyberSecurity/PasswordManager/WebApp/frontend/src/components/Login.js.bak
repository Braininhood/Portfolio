import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import styled from 'styled-components';
import { authAPI } from '../services/api';

const LoginContainer = styled.div`
  max-width: 400px;
  margin: 40px auto;
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  
  @media (max-width: 600px) {
    max-width: 100%;
    margin: 20px auto;
    padding: 1.5rem;
    border-radius: 0;
    box-shadow: none;
  }
`;

const Title = styled.h2`
  text-align: center;
  margin-bottom: 1.5rem;
  color: #333;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
`;

const FormGroup = styled.div`
  margin-bottom: 1rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: #4a6cfa;
    box-shadow: 0 0 0 2px rgba(74, 108, 250, 0.2);
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 0.75rem;
  background-color: #4a6cfa;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 1rem;
  
  &:hover {
    background-color: #3a5cf5;
  }
  
  &:disabled {
    background-color: #a0aec0;
    cursor: not-allowed;
  }
`;

const Error = styled.div`
  color: #e53e3e;
  margin-top: 0.5rem;
  font-size: 0.875rem;
`;

const Message = styled.div`
  color: #2b6cb0;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  padding: 0.5rem;
  background-color: #ebf8ff;
  border-radius: 4px;
`;

const LinkText = styled.p`
  text-align: center;
  margin-top: 1rem;
  font-size: 0.875rem;
  
  a {
    color: #4a6cfa;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [message, setMessage] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  
  // Check URL for message parameter
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const msg = params.get('message');
    if (msg) {
      setMessage(decodeURIComponent(msg));
    }
  }, []);
  
  const validateForm = () => {
    let isValid = true;
    
    // Reset errors
    setUsernameError('');
    setPasswordError('');
    setFormError('');
    
    // Validate username
    if (!username.trim()) {
      setUsernameError('Username is required');
      isValid = false;
    } else if (username.trim().length < 3) {
      setUsernameError('Username must be at least 3 characters');
      isValid = false;
    }
    
    // Validate password
    if (!password.trim()) {
      setPasswordError('Password is required');
      isValid = false;
    }
    
    return isValid;
  };
  
  const checkUserExists = async (username) => {
    try {
      // Use the authAPI instead of direct axios call
      const response = await authAPI.checkUsername(username);
      return response.data.exists;
    } catch (err) {
      console.error('Error checking username:', err);
      return null; // Return null if there was an error checking
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      // Check if user exists first
      const userExists = await checkUserExists(username);
      
      if (userExists === false) {
        // User does not exist, redirect to register
        navigate(`/register?username=${encodeURIComponent(username)}&message=${encodeURIComponent('User does not exist. Please register.')}`);
        return;
      }
      
      // Try to login
      await login(username, password);
      navigate('/vault');
    } catch (err) {
      console.error('Login error:', err);
      
      // Handle different error cases
      if (err.response?.status === 401 || err.response?.data?.error === 'Invalid credentials') {
        setPasswordError('Incorrect password. Please try again.');
      } else {
        setFormError(err.response?.data?.error || 'An error occurred during login. Please try again.');
      }
    }
  };
  
  return (
    <LoginContainer>
      <Title>Sign In</Title>
      
      {message && <Message>{message}</Message>}
      
      <Form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="username">Username</Label>
          <Input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            className={usernameError ? 'error' : ''}
            style={usernameError ? { borderColor: '#e53e3e' } : {}}
          />
          {usernameError && <Error>{usernameError}</Error>}
        </FormGroup>
        
        <FormGroup>
          <Label htmlFor="password">Password</Label>
          <Input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            className={passwordError ? 'error' : ''}
            style={passwordError ? { borderColor: '#e53e3e' } : {}}
          />
          {passwordError && <Error>{passwordError}</Error>}
        </FormGroup>
        
        {(formError || error) && (
          <Error>
            {formError || (typeof error === 'object' ? JSON.stringify(error) : error)}
          </Error>
        )}
        
        <Button type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </Button>
      </Form>
      
      <LinkText>
        Don't have an account? <Link to="/register">Register</Link>
      </LinkText>
    </LoginContainer>
  );
};

export default Login; 

