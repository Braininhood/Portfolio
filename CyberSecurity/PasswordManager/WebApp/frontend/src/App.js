import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './utils/AuthContext';
import { VaultProvider, useVault } from './utils/VaultContext';
import Login from './components/Login';
import Register from './components/Register';
import UnlockVault from './components/UnlockVault';
import Vault from './components/Vault';
import TimeoutManager from './components/TimeoutManager';
import styled from 'styled-components';

// Global styles
const AppContainer = styled.div`
  min-height: 100vh;
  background-color: #f8f9fa;
  color: #333;
  display: flex;
  flex-direction: column;
  
  @media (max-width: 768px) {
    padding-bottom: env(safe-area-inset-bottom, 0);
    padding-top: env(safe-area-inset-top, 0);
  }
`;

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Vault access route - checks if vault exists and redirects accordingly
const VaultRoute = ({ children }) => {
  const { masterKeyStatus, checkMasterKeyExists } = useVault();
  const { isAuthenticated } = useAuth();
  
  useEffect(() => {
    if (isAuthenticated() && !masterKeyStatus.exists) {
      checkMasterKeyExists();
    }
  }, [isAuthenticated, masterKeyStatus.exists, checkMasterKeyExists]);
  
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  
  if (!masterKeyStatus.exists) {
    return <Navigate to="/register-master" />;
  }
  
  if (!masterKeyStatus.unlocked) {
    return <Navigate to="/unlock" />;
  }
  
  return children;
};

const AppRoutes = () => {
  return (
    <Router>
      <AppContainer>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/unlock" 
            element={
              <ProtectedRoute>
                <UnlockVault />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/vault" 
            element={
              <VaultRoute>
                <Vault />
              </VaultRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/vault" />} />
        </Routes>
        <TimeoutManager />
      </AppContainer>
    </Router>
  );
};

function App() {
  return (
    <AuthProvider>
      <VaultProvider>
        <AppRoutes />
      </VaultProvider>
    </AuthProvider>
  );
}

export default App;
