import React, { useState } from 'react';
import styled from 'styled-components';

const EntryCard = styled.div`
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 1.25rem;
  transition: box-shadow 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  @media (max-width: 600px) {
    padding: 1rem;
  }
`;

const EntryHeader = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  
  @media (max-width: 400px) {
    flex-wrap: wrap;
  }
`;

const Website = styled.h3`
  margin: 0;
  color: #333;
  font-size: 1.1rem;
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const CardActions = styled.div`
  display: flex;
`;

const ActionButton = styled.button`
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
  margin-left: 0.25rem;
  
  &:hover {
    color: #4a6cfa;
  }
`;

const Field = styled.div`
  margin-bottom: 0.75rem;
`;

const FieldLabel = styled.span`
  display: block;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 0.25rem;
`;

const FieldValue = styled.div`
  display: flex;
  align-items: center;
  font-size: 0.95rem;
  color: #333;
`;

const PasswordValue = styled.div`
  flex-grow: 1;
  font-family: monospace;
  letter-spacing: 2px;
`;

const ToggleButton = styled.button`
  background: none;
  border: none;
  color: #4a6cfa;
  cursor: pointer;
  font-size: 0.85rem;
  margin-left: 0.5rem;
  padding: 0;
  
  &:hover {
    text-decoration: underline;
  }
`;

const CopyButton = styled.button`
  background: none;
  border: none;
  color: #4a6cfa;
  cursor: pointer;
  font-size: 0.85rem;
  margin-left: 0.5rem;
  padding: 0;
  
  &:hover {
    text-decoration: underline;
  }
`;

const Notes = styled.p`
  font-size: 0.9rem;
  color: #555;
  margin: 0.5rem 0 0;
  overflow-wrap: break-word;
`;

const CreatedAt = styled.div`
  font-size: 0.75rem;
  color: #999;
  margin-top: 1rem;
  text-align: right;
`;

const PasswordEntry = ({ entry, onEdit, onDelete }) => {
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [showCopied, setShowCopied] = useState(false);
  
  const togglePasswordVisibility = () => {
    setPasswordVisible(!passwordVisible);
  };
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setShowCopied(true);
        setTimeout(() => setShowCopied(false), 2000);
      })
      .catch(err => console.error('Failed to copy text: ', err));
  };
  
  return (
    <EntryCard style={entry.decryptionFailed ? { borderLeft: '4px solid #e53e3e' } : {}}>
      <EntryHeader>
        <Website>{entry.website}</Website>
        <CardActions>
          {!entry.decryptionFailed && (
            <>
              <ActionButton onClick={onEdit} title="Edit">✏️</ActionButton>
              <ActionButton onClick={onDelete} title="Delete">🗑️</ActionButton>
            </>
          )}
        </CardActions>
      </EntryHeader>
      
      <Field>
        <FieldLabel>Username</FieldLabel>
        <FieldValue>
          {entry.username}
          {!entry.decryptionFailed && (
            <CopyButton onClick={() => copyToClipboard(entry.username)}>
              Copy
            </CopyButton>
          )}
        </FieldValue>
      </Field>
      
      {!entry.decryptionFailed && (
        <Field>
          <FieldLabel>Password</FieldLabel>
          <FieldValue>
            <PasswordValue>
              {passwordVisible ? entry.password : '••••••••••••'}
            </PasswordValue>
            <ToggleButton onClick={togglePasswordVisibility}>
              {passwordVisible ? 'Hide' : 'Show'}
            </ToggleButton>
            <CopyButton onClick={() => copyToClipboard(entry.password)}>
              {showCopied ? 'Copied!' : 'Copy'}
            </CopyButton>
          </FieldValue>
        </Field>
      )}
      
      {entry.notes && (
        <Field>
          <FieldLabel>Notes</FieldLabel>
          <Notes>{entry.notes}</Notes>
        </Field>
      )}
      
      <CreatedAt>
        Created: {formatDate(entry.created_at)}
      </CreatedAt>
    </EntryCard>
  );
};

export default PasswordEntry; 