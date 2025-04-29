import React from 'react';
import styled from 'styled-components';

const ErrorContainer = styled.div`
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
`;

const ErrorIcon = styled.span`
  color: #EF4444;
  font-size: 20px;
`;

const ErrorText = styled.p`
  margin: 0;
  color: #EF4444;
  font-size: 14px;
  text-align: center;
  font-weight: 500;
`;

const HelpText = styled.p`
  margin: 0;
  color: #6B7280;
  font-size: 12px;
  text-align: center;
`;

const DecryptionError = () => {
  return (
    <ErrorContainer>
      <ErrorIcon aria-hidden="true">🔒</ErrorIcon>
      <ErrorText>Decryption Failed</ErrorText>
      <HelpText>This entry could not be decrypted with your current key</HelpText>
    </ErrorContainer>
  );
};

export default DecryptionError; 