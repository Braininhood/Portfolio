import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { useVault } from '../utils/VaultContext';
import styled from 'styled-components';
import axios from 'axios';

const RegisterContainer = styled.div`
  max-width: 500px;
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
  margin-bottom: 1rem;
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

const PasswordStrength = styled.div`
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: ${props => {
    if (props.score >= 4) return '#38a169'; // Strong (green)
    if (props.score >= 3) return '#68d391'; // Good (light green)
    if (props.score >= 2) return '#f6ad55'; // Fair (orange)
    return '#f56565'; // Weak (red)
  }};
`;

const Register = () => {
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [masterPassword, setMasterPassword] = useState('');
  const [confirmMasterPassword, setConfirmMasterPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [message, setMessage] = useState('');
  
  // Input validation errors
  const [usernameError, setUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [masterPasswordError, setMasterPasswordError] = useState('');
  const [confirmMasterPasswordError, setConfirmMasterPasswordError] = useState('');
  
  const { register, loading: authLoading, error: authError } = useAuth();
  const { createMasterKey, loading: vaultLoading, error: vaultError } = useVault();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Check URL parameters
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const usernameParam = params.get('username');
    const messageParam = params.get('message');
    
    if (usernameParam) {
      setUsername(usernameParam);
    }
    
    if (messageParam) {
      setMessage(decodeURIComponent(messageParam));
    }
  }, [location]);
  
  const calculatePasswordStrength = (pass) => {
    if (!pass) return 0;
    
    let score = 0;
    
    // Length
    if (pass.length >= 8) score += 1;
    if (pass.length >= 12) score += 1;
    
    // Complexity
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;
    
    return Math.min(score, 5);
  };
  
  const passwordScore = calculatePasswordStrength(password);
  const masterPasswordScore = calculatePasswordStrength(masterPassword);
  
  const getPasswordStrengthText = (score) => {
    if (score >= 4) return 'Strong';
    if (score >= 3) return 'Good';
    if (score >= 2) return 'Fair';
    if (score >= 1) return 'Weak';
    return 'Very Weak';
  };
  
  const checkUserExists = async (username) => {
    try {
      const response = await axios.post('http://localhost:8000/api/check-username/', { username });
      return response.data.exists;
    } catch (err) {
      console.error('Error checking username:', err);
      return null;
    }
  };
  
  const validateAccountForm = () => {
    let isValid = true;
    
    // Reset errors
    setUsernameError('');
    setEmailError('');
    setPasswordError('');
    setConfirmPasswordError('');
    setFormError('');
    
    // Validate username
    if (!username.trim()) {
      setUsernameError('Username is required');
      isValid = false;
    } else if (username.trim().length < 3) {
      setUsernameError('Username must be at least 3 characters');
      isValid = false;
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setUsernameError('Username can only contain letters, numbers, and underscores');
      isValid = false;
    }
    
    // Validate email
    if (!email.trim()) {
      setEmailError('Email is required');
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setEmailError('Please enter a valid email address');
      isValid = false;
    }
    
    // Validate password
    if (!password) {
      setPasswordError('Password is required');
      isValid = false;
    } else if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      isValid = false;
    } else if (passwordScore < 3) {
      setPasswordError('Please use a stronger password with a mix of uppercase, lowercase, numbers, and symbols');
      isValid = false;
    }
    
    // Validate confirm password
    if (!confirmPassword) {
      setConfirmPasswordError('Please confirm your password');
      isValid = false;
    } else if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      isValid = false;
    }
    
    return isValid;
  };
  
  const validateMasterPasswordForm = () => {
    let isValid = true;
    
    // Reset errors
    setMasterPasswordError('');
    setConfirmMasterPasswordError('');
    setFormError('');
    
    // Validate master password
    if (!masterPassword) {
      setMasterPasswordError('Master password is required');
      isValid = false;
    } else if (masterPassword.length < 10) {
      setMasterPasswordError('Master password must be at least 10 characters');
      isValid = false;
    } else if (masterPasswordScore < 4) {
      setMasterPasswordError('Your master password is too weak. This password protects all your other passwords, so it needs to be very strong.');
      isValid = false;
    }
    
    // Validate confirm master password
    if (!confirmMasterPassword) {
      setConfirmMasterPasswordError('Please confirm your master password');
      isValid = false;
    } else if (masterPassword !== confirmMasterPassword) {
      setConfirmMasterPasswordError('Master passwords do not match');
      isValid = false;
    }
    
    return isValid;
  };
  
  const handleAccountSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateAccountForm()) {
      return;
    }
    
    // Check if user already exists
    const userExists = await checkUserExists(username);
    
    if (userExists) {
      // User exists, redirect to login
      navigate(`/login?message=${encodeURIComponent('User already exists. Please login.')}`);
      return;
    }
    
    // Move to master password step
    setStep(2);
  };
  
  const handleMasterPasswordSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateMasterPasswordForm()) {
      return;
    }
    
    try {
      // Register user
      await register(username, email, password);
      
      // Set up master key
      await createMasterKey(masterPassword);
      
      // Redirect to vault
      navigate('/vault');
    } catch (err) {
      console.error('Registration error:', err);
      
      // Handle different error cases
      if (err.response?.data?.username) {
        setFormError(`Username error: ${err.response.data.username}`);
      } else if (err.response?.data?.email) {
        setFormError(`Email error: ${err.response.data.email}`);
      } else if (err.response?.data?.password) {
        setFormError(`Password error: ${err.response.data.password}`);
      } else {
        setFormError(err.response?.data?.error || 'Registration failed. Please try again.');
      }
    }
  };
  
  return (
    <RegisterContainer>
      <Title>{step === 1 ? 'Create Account' : 'Set Master Password'}</Title>
      
      {message && <Message>{message}</Message>}
      
      {step === 1 ? (
        <Form onSubmit={handleAccountSubmit}>
          <FormGroup>
            <Label htmlFor="username">Username</Label>
            <Input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              style={usernameError ? { borderColor: '#e53e3e' } : {}}
            />
            {usernameError && <Error>{usernameError}</Error>}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="email">Email</Label>
            <Input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              style={emailError ? { borderColor: '#e53e3e' } : {}}
            />
            {emailError && <Error>{emailError}</Error>}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a password"
              style={passwordError ? { borderColor: '#e53e3e' } : {}}
            />
            {passwordScore > 0 && (
              <PasswordStrength score={passwordScore}>
                Password Strength: {getPasswordStrengthText(passwordScore)}
              </PasswordStrength>
            )}
            {passwordError && <Error>{passwordError}</Error>}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              style={confirmPasswordError ? { borderColor: '#e53e3e' } : {}}
            />
            {confirmPasswordError && <Error>{confirmPasswordError}</Error>}
          </FormGroup>
          
          {formError && <Error>{formError}</Error>}
          
          <Button type="submit" disabled={authLoading}>
            {authLoading ? 'Processing...' : 'Continue'}
          </Button>
        </Form>
      ) : (
        <Form onSubmit={handleMasterPasswordSubmit}>
          <p style={{ marginBottom: '1rem' }}>
            Your master password is the key to your encrypted vault. 
            It is <strong>never</strong> sent to our servers and 
            <strong> cannot be recovered</strong> if you forget it.
          </p>
          
          <FormGroup>
            <Label htmlFor="masterPassword">Master Password</Label>
            <Input
              type="password"
              id="masterPassword"
              value={masterPassword}
              onChange={(e) => setMasterPassword(e.target.value)}
              placeholder="Create a strong master password"
              style={masterPasswordError ? { borderColor: '#e53e3e' } : {}}
            />
            {masterPassword && (
              <PasswordStrength score={masterPasswordScore}>
                Master Password Strength: {getPasswordStrengthText(masterPasswordScore)}
              </PasswordStrength>
            )}
            {masterPasswordError && <Error>{masterPasswordError}</Error>}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="confirmMasterPassword">Confirm Master Password</Label>
            <Input
              type="password"
              id="confirmMasterPassword"
              value={confirmMasterPassword}
              onChange={(e) => setConfirmMasterPassword(e.target.value)}
              placeholder="Confirm your master password"
              style={confirmMasterPasswordError ? { borderColor: '#e53e3e' } : {}}
            />
            {confirmMasterPasswordError && <Error>{confirmMasterPasswordError}</Error>}
          </FormGroup>
          
          {(formError || authError || vaultError) && (
            <Error>
              {formError || 
               (typeof authError === 'object' ? JSON.stringify(authError) : authError) || 
               (typeof vaultError === 'object' ? JSON.stringify(vaultError) : vaultError)}
            </Error>
          )}
          
          <Button type="submit" disabled={authLoading || vaultLoading}>
            {authLoading || vaultLoading ? 'Creating Account...' : 'Create Account'}
          </Button>
          
          <Button 
            type="button" 
            onClick={() => setStep(1)} 
            style={{ 
              backgroundColor: 'transparent', 
              color: '#4a6cfa',
              marginTop: '0.5rem',
              border: '1px solid #4a6cfa'
            }}
          >
            Back
          </Button>
        </Form>
      )}
      
      <LinkText>
        Already have an account? <Link to="/login">Sign In</Link>
      </LinkText>
    </RegisterContainer>
  );
};

export default Register; 