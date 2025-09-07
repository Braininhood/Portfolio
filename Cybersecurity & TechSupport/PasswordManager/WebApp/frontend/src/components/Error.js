import React from 'react';
import styled from 'styled-components';

const ErrorContainer = styled.div`
  background-color: #FEE2E2;
  border-left: 4px solid #EF4444;
  color: #B91C1C;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  align-items: center;
  animation: fadeIn 0.3s ease-in-out;
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @media (max-width: 768px) {
    font-size: 13px;
    padding: 10px 12px;
  }
`;

const ErrorIcon = styled.span`
  margin-right: 10px;
  font-size: 18px;
`;

const ErrorText = styled.p`
  margin: 0;
  flex: 1;
`;

const Error = ({ message }) => {
  return (
    <ErrorContainer role="alert">
      <ErrorIcon aria-hidden="true">⚠️</ErrorIcon>
      <ErrorText>{message}</ErrorText>
    </ErrorContainer>
  );
};

export default Error; 