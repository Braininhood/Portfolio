import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVault } from '../utils/VaultContext';
import { useAuth } from '../utils/AuthContext';
import styled from 'styled-components';

const UnlockContainer = styled.div`
  max-width: 450px;
  margin: 40px auto;
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  
  @media (max-width: 600px) {
    max-width: 100%;
    margin: 20px auto;
    padding: 1.5rem;
  }
`;

const Title = styled.h2`
  margin-bottom: 1rem;
  color: #333;
`;

const Description = styled.p`
  margin-bottom: 1.5rem;
  color: #555;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 1rem;
  
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
  
  &:hover {
    background-color: #3a5cf5;
  }
  
  &:disabled {
    background-color: #a0aec0;
    cursor: not-allowed;
  }
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: #4a6cfa;
  cursor: pointer;
  font-size: 0.9rem;
  margin-top: 1rem;
  text-decoration: underline;
  
  &:hover {
    color: #3a5cf5;
  }
`;

const Error = styled.div`
  color: #e53e3e;
  margin-bottom: 1rem;
  font-size: 0.875rem;
`;

const LoadingSpinner = styled.div`
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4a6cfa;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const UnlockVault = () => {
  const [masterPassword, setMasterPassword] = useState('');
  const [error, setError] = useState('');
  const { masterKeyStatus, unlockVault, loading } = useVault();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  useEffect(() => {
    // If vault is already unlocked, go to vault page
    if (masterKeyStatus.unlocked) {
      navigate('/vault');
    }
  }, [masterKeyStatus, navigate]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!masterPassword) {
      setError('Please enter your master password');
      return;
    }
    
    try {
      await unlockVault(masterPassword);
      navigate('/vault');
    } catch (err) {
      console.error('Unlock error:', err);
      setError('Invalid master password');
    }
  };
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <UnlockContainer>
      <Title>Unlock Your Vault</Title>
      <Description>
        Enter your master password to access your secure vault.
      </Description>
      
      <Form onSubmit={handleSubmit}>
        {error && <Error>{error}</Error>}
        
        <Input
          type="password"
          placeholder="Enter your master password"
          value={masterPassword}
          onChange={(e) => setMasterPassword(e.target.value)}
          autoFocus
        />
        
        <Button type="submit" disabled={loading}>
          {loading ? <LoadingSpinner /> : 'Unlock'}
        </Button>
      </Form>
      
      <LogoutButton onClick={handleLogout}>
        Sign out ({user?.username})
      </LogoutButton>
    </UnlockContainer>
  );
};

export default UnlockVault; 