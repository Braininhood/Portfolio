import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useVault } from '../utils/VaultContext';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: #fff;
  border-radius: 8px;
  padding: 2rem;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  
  @media (max-width: 600px) {
    max-width: 100%;
    margin: 0 1rem;
    padding: 1.5rem;
    max-height: 90vh;
    overflow-y: auto;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const ModalTitle = styled.h2`
  margin: 0;
  color: #333;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  
  &:hover {
    color: #333;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
`;

const FormGroup = styled.div`
  margin-bottom: 1.25rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
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

const Textarea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;
  
  &:focus {
    outline: none;
    border-color: #4a6cfa;
    box-shadow: 0 0 0 2px rgba(74, 108, 250, 0.2);
  }
`;

const Button = styled.button`
  padding: 0.75rem 1rem;
  background-color: ${props => props.secondary ? 'transparent' : '#4a6cfa'};
  color: ${props => props.secondary ? '#4a6cfa' : 'white'};
  border: ${props => props.secondary ? '1px solid #4a6cfa' : 'none'};
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.secondary ? '#f0f5ff' : '#3a5cf5'};
  }
  
  &:disabled {
    background-color: #a0aec0;
    cursor: not-allowed;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
  
  @media (max-width: 400px) {
    flex-direction: column-reverse;
  }
`;

const PasswordRow = styled.div`
  display: flex;
  gap: 0.5rem;
  
  @media (max-width: 400px) {
    flex-direction: column;
  }
`;

const GenerateButton = styled.button`
  background-color: #edf2ff;
  color: #4a6cfa;
  border: none;
  border-radius: 4px;
  padding: 0.5rem;
  cursor: pointer;
  font-size: 0.85rem;
  
  &:hover {
    background-color: #dbe4ff;
  }
`;

const Error = styled.div`
  color: #e53e3e;
  margin-top: 0.5rem;
  font-size: 0.875rem;
`;

const AddPasswordModal = ({ onClose, editingEntry }) => {
  const [website, setWebsite] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  
  const { addEntry, updateEntry, generatePassword, loading } = useVault();
  
  useEffect(() => {
    // Fill form with data if editing an existing entry
    if (editingEntry) {
      setWebsite(editingEntry.website || '');
      setUsername(editingEntry.username || '');
      setPassword(editingEntry.password || '');
      setNotes(editingEntry.notes || '');
    }
  }, [editingEntry]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!website || !username || !password) {
      setError('Please fill in all required fields');
      return;
    }
    
    try {
      const entryData = {
        website,
        username,
        password,
        notes
      };
      
      if (editingEntry) {
        await updateEntry(editingEntry.id, entryData);
      } else {
        await addEntry(entryData);
      }
      
      onClose();
    } catch (err) {
      console.error('Error saving password:', err);
      // More detailed error message
      if (err.response?.data) {
        setError(`Failed to save password: ${JSON.stringify(err.response.data)}`);
      } else if (err.message) {
        setError(`Failed to save password: ${err.message}`);
      } else {
        setError('Failed to save password. Please try again.');
      }
    }
  };
  
  const handleGeneratePassword = () => {
    const newPassword = generatePassword(16);
    setPassword(newPassword);
  };
  
  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <ModalHeader>
          <ModalTitle>{editingEntry ? 'Edit Password' : 'Add Password'}</ModalTitle>
          <CloseButton onClick={onClose}>&times;</CloseButton>
        </ModalHeader>
        
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="website">Website / Application *</Label>
            <Input
              type="text"
              id="website"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="e.g. facebook.com"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="username">Username / Email *</Label>
            <Input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. john.doe@example.com"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="password">Password *</Label>
            <PasswordRow>
              <Input
                type="text"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
              <GenerateButton 
                type="button" 
                onClick={handleGeneratePassword}
                title="Generate a strong password"
              >
                Generate
              </GenerateButton>
            </PasswordRow>
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add additional notes here"
            />
          </FormGroup>
          
          {error && <Error>{error}</Error>}
          
          <ButtonGroup>
            <Button type="button" secondary onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : editingEntry ? 'Update' : 'Save'}
            </Button>
          </ButtonGroup>
        </Form>
      </ModalContent>
    </ModalOverlay>
  );
};

export default AddPasswordModal; 