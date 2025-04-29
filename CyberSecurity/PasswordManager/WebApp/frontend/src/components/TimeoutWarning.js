import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';

const WarningContainer = styled.div`
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: #f8d7da;
  color: #721c24;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: ${props => (props.visible ? 'block' : 'none')};
  animation: fadeIn 0.3s ease-in;
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const WarningTitle = styled.h4`
  margin: 0 0 10px 0;
  font-size: 16px;
`;

const WarningText = styled.p`
  margin: 0 0 10px 0;
  font-size: 14px;
`;

const ButtonContainer = styled.div`
  display: flex;
  justify-content: flex-end;
`;

const Button = styled.button`
  background-color: #721c24;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  
  &:hover {
    background-color: #5c171e;
  }
`;

const TimeoutWarning = ({ 
  timeoutSoon = false,
  timeoutInSeconds = 30,
  onContinue = () => {} 
}) => {
  const [visible, setVisible] = useState(false);
  const [countdown, setCountdown] = useState(timeoutInSeconds);
  const intervalRef = useRef(null);
  
  useEffect(() => {
    if (timeoutSoon) {
      setVisible(true);
      setCountdown(timeoutInSeconds);
      
      // Start countdown
      intervalRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(intervalRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      setVisible(false);
      clearInterval(intervalRef.current);
    }
    
    return () => {
      clearInterval(intervalRef.current);
    };
  }, [timeoutSoon, timeoutInSeconds]);
  
  const handleContinue = () => {
    setVisible(false);
    onContinue();
  };
  
  return (
    <WarningContainer visible={visible}>
      <WarningTitle>Session Timeout Warning</WarningTitle>
      <WarningText>
        Due to inactivity, your session will expire in {countdown} seconds.
      </WarningText>
      <ButtonContainer>
        <Button onClick={handleContinue}>Continue Session</Button>
      </ButtonContainer>
    </WarningContainer>
  );
};

export default TimeoutWarning; 