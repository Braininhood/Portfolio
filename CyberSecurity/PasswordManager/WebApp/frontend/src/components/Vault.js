import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVault } from '../utils/VaultContext';
import { useAuth } from '../utils/AuthContext';
import styled from 'styled-components';
import PasswordEntry from './PasswordEntry';
import AddPasswordModal from './AddPasswordModal';

const VaultContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  @media (max-width: 600px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
`;

const Title = styled.h1`
  color: #333;
  margin: 0;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  
  @media (max-width: 600px) {
    width: 100%;
    justify-content: space-between;
  }
  
  @media (max-width: 400px) {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
`;

const Username = styled.span`
  margin-right: 1rem;
  font-weight: 600;
`;

const Button = styled.button`
  padding: 0.5rem 1rem;
  background-color: ${props => props.secondary ? 'transparent' : '#4a6cfa'};
  color: ${props => props.secondary ? '#4a6cfa' : 'white'};
  border: ${props => props.secondary ? '1px solid #4a6cfa' : 'none'};
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  margin-left: 0.5rem;
  
  &:hover {
    background-color: ${props => props.secondary ? '#f0f5ff' : '#3a5cf5'};
  }
`;

const SearchBar = styled.div`
  width: 100%;
  margin-bottom: 1.5rem;
`;

const SearchInput = styled.input`
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

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-top: 2rem;
`;

const EmptyStateTitle = styled.h3`
  margin-bottom: 1rem;
  color: #333;
`;

const PasswordGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
`;

const LoadingSpinner = styled.div`
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4a6cfa;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const Vault = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  
  const { 
    masterKeyStatus, 
    entries, 
    loading, 
    lockVault, 
    loadEntries,
    deleteEntry
  } = useVault();
  
  const { 
    user, 
    logout
  } = useAuth();
  
  const navigate = useNavigate();
  
  useEffect(() => {
    // Check if vault is unlocked
    if (!masterKeyStatus.unlocked) {
      navigate('/unlock');
      return;
    }
    
    // Load entries if not already loaded
    if (entries.length === 0 && !loading) {
      loadEntries();
    }
    // We intentionally omit entries.length, loading and loadEntries as dependencies
    // to prevent a loop of API calls. masterKeyStatus.unlocked is the key dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [masterKeyStatus.unlocked, navigate]);
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const handleLockVault = () => {
    lockVault();
    navigate('/unlock');
  };
  
  const handleAddPassword = () => {
    setEditingEntry(null);
    setShowAddModal(true);
  };
  
  const handleEditPassword = (entry) => {
    setEditingEntry(entry);
    setShowAddModal(true);
  };
  
  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingEntry(null);
  };
  
  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this password?')) {
      try {
        await deleteEntry(id);
      } catch (err) {
        console.error('Delete error:', err);
      }
    }
  };
  
  // Filter entries by search term
  const filteredEntries = entries.filter(entry => {
    // Don't filter entries that had decryption errors
    if (entry.decryptionFailed) return true;
    
    const searchFields = [
      entry.website?.toLowerCase(),
      entry.username?.toLowerCase(),
      entry.notes?.toLowerCase()
    ].filter(Boolean);
    
    return searchFields.some(field => field.includes(searchTerm.toLowerCase()));
  });
  
  return (
    <VaultContainer>
      <Header>
        <Title>Password Vault</Title>
        <UserInfo>
          <Username>{user?.username}</Username>
          <Button secondary onClick={handleLockVault}>Lock Vault</Button>
          <Button secondary onClick={handleLogout}>Sign Out</Button>
        </UserInfo>
      </Header>
      
      <SearchBar>
        <SearchInput 
          type="text" 
          placeholder="Search passwords..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </SearchBar>
      
      <Button onClick={handleAddPassword}>Add Password</Button>
      
      {loading ? (
        <LoadingContainer>
          <LoadingSpinner />
        </LoadingContainer>
      ) : entries.length === 0 ? (
        <EmptyState>
          <EmptyStateTitle>Your vault is empty</EmptyStateTitle>
          <p>Add your first password to get started.</p>
          <Button onClick={handleAddPassword}>Add Your First Password</Button>
        </EmptyState>
      ) : (
        <PasswordGrid>
          {filteredEntries.map(entry => (
            <PasswordEntry 
              key={entry.id} 
              entry={entry} 
              onEdit={() => handleEditPassword(entry)}
              onDelete={() => handleDelete(entry.id)}
            />
          ))}
        </PasswordGrid>
      )}
      
      {showAddModal && (
        <AddPasswordModal 
          onClose={handleCloseModal} 
          editingEntry={editingEntry}
        />
      )}
    </VaultContainer>
  );
};

export default Vault; 