import React, { createContext, useState, useContext, useEffect, useRef, useCallback } from 'react';
import { authAPI, vaultAPI, passwordEntriesAPI } from '../services/api';
import * as crypto from './cryptoUtils';

// Create context for the vault
const VaultContext = createContext();

// Auto-lock timeout in milliseconds (2 minutes)
const AUTO_LOCK_TIMEOUT = 2 * 60 * 1000;
const WARNING_BEFORE_LOCK = 30 * 1000; // Show warning 30 seconds before locking

export const VaultProvider = ({ children }) => {
  const [masterKeyStatus, setMasterKeyStatus] = useState(() => {
    const status = localStorage.getItem('masterKeyStatus');
    return status ? JSON.parse(status) : { exists: false, unlocked: false };
  });
  
  const [vaultKey, setVaultKey] = useState(null);
  const [vault, setVault] = useState(null);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Timer for auto-lock
  const autoLockTimerRef = useRef(null);
  const warningTimerRef = useRef(null);
  // eslint-disable-next-line no-unused-vars
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showLockWarning, setShowLockWarning] = useState(false);
  
  // Define lockVault function with useCallback to avoid dependency changes
  const lockVault = useCallback(() => {
    setVaultKey(null);
    setMasterKeyStatus({ ...masterKeyStatus, unlocked: false });
    localStorage.setItem('masterKeyStatus', JSON.stringify({ ...masterKeyStatus, unlocked: false }));
  }, [masterKeyStatus]);
  
  // Reset the auto-lock timer when there's user activity
  const resetAutoLockTimer = useCallback(() => {
    setLastActivity(Date.now());
    setShowLockWarning(false);
    
    // Clear both timers
    if (autoLockTimerRef.current) {
      clearTimeout(autoLockTimerRef.current);
      autoLockTimerRef.current = null;
    }
    
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    
    if (masterKeyStatus.unlocked && vaultKey) {
      // Set timer for warning
      warningTimerRef.current = setTimeout(() => {
        setShowLockWarning(true);
      }, AUTO_LOCK_TIMEOUT - WARNING_BEFORE_LOCK);
      
      // Set timer for auto-lock
      autoLockTimerRef.current = setTimeout(() => {
        console.log('Auto-locking vault due to inactivity');
        lockVault();
        setShowLockWarning(false);
      }, AUTO_LOCK_TIMEOUT);
    }
  }, [masterKeyStatus.unlocked, vaultKey, lockVault]);
  
  // Reset the timer when user continues the session
  const continueVaultSession = useCallback(() => {
    resetAutoLockTimer();
  }, [resetAutoLockTimer]);
  
  // Monitor for user activity
  useEffect(() => {
    const handleActivity = () => {
      resetAutoLockTimer();
    };
    
    // Track user activity
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);
    window.addEventListener('scroll', handleActivity);
    
    // Set initial timer
    resetAutoLockTimer();
    
    return () => {
      // Clean up event listeners
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('scroll', handleActivity);
      
      // Clear timer on unmount
      if (autoLockTimerRef.current) {
        clearTimeout(autoLockTimerRef.current);
      }
    };
  }, [masterKeyStatus.unlocked, vaultKey, resetAutoLockTimer]);
  
  // Create master key during registration
  const createMasterKey = async (masterPassword) => {
    setLoading(true);
    setError(null);
    
    try {
      // Generate salt for key derivation
      const salt = crypto.generateSalt();
      
      // Derive master key from password and salt
      const masterKey = crypto.deriveKeyFromPassword(masterPassword, salt);
      
      // Generate verification hash
      const verificationHash = crypto.generateVerificationHash(masterKey);
      
      // Save salt and verification hash on server
      await authAPI.setupMasterKey(salt, verificationHash);
      
      // Generate a random vault key
      const newVaultKey = crypto.generateVaultKey();
      
      // Encrypt vault key with master key
      const vaultKeyEncrypted = crypto.encryptVaultKey(newVaultKey, masterKey);
      
      // Create new vault
      const vaultResponse = await vaultAPI.createVault(vaultKeyEncrypted, salt);
      
      // Update state
      setVaultKey(newVaultKey);
      setVault(vaultResponse.data);
      setMasterKeyStatus({ exists: true, unlocked: true });
      
      // Store master key status in localStorage
      localStorage.setItem('masterKeyStatus', JSON.stringify({ exists: true, unlocked: true }));
      
      return true;
    } catch (err) {
      setError(err.response?.data || 'Failed to create master key');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Unlock vault with master password
  const unlockVault = async (masterPassword) => {
    setLoading(true);
    setError(null);
    
    try {
      // Get salt from server
      const saltResponse = await authAPI.getMasterKeySalt();
      const salt = saltResponse.data.salt;
      
      // Derive master key from password and salt
      const masterKey = crypto.deriveKeyFromPassword(masterPassword, salt);
      
      // Generate verification hash
      const verificationHash = crypto.generateVerificationHash(masterKey);
      
      // Verify master key
      const verifyResponse = await authAPI.verifyMasterKey(verificationHash);
      
      if (!verifyResponse.data.valid) {
        throw new Error('Invalid master password');
      }
      
      // Get vault data
      const vaultResponse = await vaultAPI.getVault();
      const vaultData = vaultResponse.data[0]; // Assuming one vault per user
      
      // Decrypt vault key
      const decryptedVaultKey = crypto.decryptVaultKey(
        vaultData.vault_key_encrypted,
        masterKey
      );
      
      // Set state
      setVaultKey(decryptedVaultKey);
      setVault(vaultData);
      setMasterKeyStatus({ exists: true, unlocked: true });
      
      // Store master key status in localStorage
      localStorage.setItem('masterKeyStatus', JSON.stringify({ exists: true, unlocked: true }));
      
      // Load password entries
      await loadEntries(decryptedVaultKey);
      
      return true;
    } catch (err) {
      setError(err.response?.data || err.message || 'Failed to unlock vault');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Check if master key exists
  const checkMasterKeyExists = async () => {
    try {
      await authAPI.getMasterKeySalt();
      setMasterKeyStatus({ exists: true, unlocked: false });
      localStorage.setItem('masterKeyStatus', JSON.stringify({ exists: true, unlocked: false }));
      return true;
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setMasterKeyStatus({ exists: false, unlocked: false });
        localStorage.setItem('masterKeyStatus', JSON.stringify({ exists: false, unlocked: false }));
        return false;
      }
      throw err;
    }
  };
  
  // Load password entries
  const loadEntries = async (currentVaultKey) => {
    setLoading(true);
    
    try {
      // Check if we have a valid vault key
      const vaultKeyToUse = currentVaultKey || vaultKey;
      if (!vaultKeyToUse) {
        console.warn('Cannot load entries: Vault key is not available');
        setEntries([]);
        return [];
      }
      
      const response = await passwordEntriesAPI.getEntries();
      
      // If no entries yet, return empty array
      if (!response.data || response.data.length === 0) {
        setEntries([]);
        return [];
      }
      
      // Decrypt entries with vault key
      const decryptedEntries = response.data.map(entry => {
        try {
          const decryptedData = crypto.decryptData(
            entry.encrypted_data,
            entry.iv,
            vaultKeyToUse
          );
          
          return {
            id: entry.id,
            ...decryptedData,
            encrypted_data: entry.encrypted_data,
            iv: entry.iv,
            created_at: entry.created_at,
            updated_at: entry.updated_at
          };
        } catch (decryptError) {
          console.error('Failed to decrypt entry:', decryptError);
          // Return a placeholder for failed entries
          return {
            id: entry.id,
            website: 'Decryption Error',
            username: 'Could not decrypt',
            password: '',
            notes: 'This entry could not be decrypted. The vault may need to be unlocked.',
            encrypted_data: entry.encrypted_data,
            iv: entry.iv,
            created_at: entry.created_at,
            updated_at: entry.updated_at,
            decryptionFailed: true
          };
        }
      });
      
      setEntries(decryptedEntries);
      return decryptedEntries;
    } catch (err) {
      console.error('Error loading entries:', err);
      setError(err.response?.data || 'Failed to load entries');
      setEntries([]);
      return [];
    } finally {
      setLoading(false);
    }
  };
  
  // Add new password entry
  const addEntry = async (entryData) => {
    if (!vaultKey) {
      throw new Error('Vault is locked');
    }
    
    setLoading(true);
    
    try {
      // Encrypt entry data
      const { encryptedData, iv } = crypto.encryptData(entryData, vaultKey);
      
      // Save to server
      const response = await passwordEntriesAPI.createEntry(encryptedData, iv);
      
      // Add decrypted entry to state
      const newEntry = {
        id: response.data.id,
        ...entryData,
        encrypted_data: encryptedData,
        iv: iv,
        created_at: response.data.created_at,
        updated_at: response.data.updated_at
      };
      
      setEntries([...entries, newEntry]);
      return newEntry;
    } catch (err) {
      setError(err.response?.data || 'Failed to add entry');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Update password entry
  const updateEntry = async (id, entryData) => {
    if (!vaultKey) {
      throw new Error('Vault is locked');
    }
    
    setLoading(true);
    
    try {
      // Encrypt entry data
      const { encryptedData, iv } = crypto.encryptData(entryData, vaultKey);
      
      // Save to server
      const response = await passwordEntriesAPI.updateEntry(id, encryptedData, iv);
      
      // Update entry in state
      const updatedEntries = entries.map(entry => 
        entry.id === id 
          ? {
              ...entry,
              ...entryData,
              encrypted_data: encryptedData,
              iv: iv,
              updated_at: response.data.updated_at
            } 
          : entry
      );
      
      setEntries(updatedEntries);
      return updatedEntries.find(entry => entry.id === id);
    } catch (err) {
      setError(err.response?.data || 'Failed to update entry');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Delete password entry
  const deleteEntry = async (id) => {
    setLoading(true);
    
    try {
      await passwordEntriesAPI.deleteEntry(id);
      
      // Remove entry from state
      const updatedEntries = entries.filter(entry => entry.id !== id);
      setEntries(updatedEntries);
      
      return true;
    } catch (err) {
      setError(err.response?.data || 'Failed to delete entry');
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  // Generate a random password
  const generatePassword = (length = 16) => {
    return crypto.generateRandomPassword(length);
  };
  
  return (
    <VaultContext.Provider
      value={{
        masterKeyStatus,
        vault,
        entries,
        loading,
        error,
        createMasterKey,
        unlockVault,
        lockVault,
        checkMasterKeyExists,
        loadEntries,
        addEntry,
        updateEntry,
        deleteEntry,
        generatePassword,
        showLockWarning,
        continueVaultSession
      }}
    >
      {children}
    </VaultContext.Provider>
  );
};

// Custom hook to use the vault context
export const useVault = () => {
  const context = useContext(VaultContext);
  if (!context) {
    throw new Error('useVault must be used within a VaultProvider');
  }
  return context;
}; 