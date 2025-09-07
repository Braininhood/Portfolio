import React, { useState } from 'react';
import { useAuth } from '../utils/AuthContext';
import { useVault } from '../utils/VaultContext';
import TimeoutWarning from './TimeoutWarning';

// This component manages timeout warnings across the application
const TimeoutManager = () => {
  const [showingLockWarning, setShowingLockWarning] = useState(false);
  
  const { 
    isAuthenticated,
    showSignoutWarning, 
    continueAuthSession 
  } = useAuth();
  
  const { 
    masterKeyStatus,
    showLockWarning, 
    continueVaultSession 
  } = useVault();
  
  // Don't show anything if not authenticated
  if (!isAuthenticated()) {
    return null;
  }
  
  // Only show one warning at a time
  const handleVaultContinue = () => {
    continueVaultSession();
    setShowingLockWarning(true); // Remember we showed the lock warning
  };
  
  // Decide which warning to show (prioritize auth warning over lock warning)
  const shouldShowLockWarning = showLockWarning && masterKeyStatus.unlocked && !showSignoutWarning && !showingLockWarning;
  
  return (
    <>
      {/* Vault lock warning - only show if vault is unlocked and not showing signout warning */}
      <TimeoutWarning 
        timeoutSoon={shouldShowLockWarning} 
        timeoutInSeconds={30}
        onContinue={handleVaultContinue}
      />
      
      {/* Auth signout warning - show on any authenticated page */}
      <TimeoutWarning 
        timeoutSoon={showSignoutWarning} 
        timeoutInSeconds={30}
        onContinue={continueAuthSession}
      />
    </>
  );
};

export default TimeoutManager; 