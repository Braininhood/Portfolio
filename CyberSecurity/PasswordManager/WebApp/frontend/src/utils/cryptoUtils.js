import CryptoJS from 'crypto-js';

/**
 * Crypto utilities for zero-knowledge password management
 * All encryption/decryption happens client-side
 */

// Generate a random salt for key derivation
export const generateSalt = () => {
  return CryptoJS.lib.WordArray.random(128 / 8).toString(CryptoJS.enc.Hex);
};

// Derive a key from the master password using PBKDF2
export const deriveKeyFromPassword = (password, salt, iterations = 10000) => {
  return CryptoJS.PBKDF2(password, salt, {
    keySize: 256 / 32,
    iterations
  }).toString(CryptoJS.enc.Hex);
};

// Generate a verification hash to verify correct master password
export const generateVerificationHash = (derivedKey) => {
  const verificationData = 'password-manager-verification';
  return CryptoJS.HmacSHA256(verificationData, derivedKey).toString(CryptoJS.enc.Hex);
};

// Generate a random encryption key for the vault
export const generateVaultKey = () => {
  return CryptoJS.lib.WordArray.random(256 / 8).toString(CryptoJS.enc.Hex);
};

// Encrypt the vault key with the master key
export const encryptVaultKey = (vaultKey, masterKey) => {
  return CryptoJS.AES.encrypt(vaultKey, masterKey).toString();
};

// Decrypt the vault key with the master key
export const decryptVaultKey = (encryptedVaultKey, masterKey) => {
  const bytes = CryptoJS.AES.decrypt(encryptedVaultKey, masterKey);
  return bytes.toString(CryptoJS.enc.Utf8);
};

// Encrypt data with the vault key
export const encryptData = (data, vaultKey) => {
  const iv = CryptoJS.lib.WordArray.random(128 / 8);
  const encrypted = CryptoJS.AES.encrypt(JSON.stringify(data), vaultKey, {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  });
  
  return {
    encryptedData: encrypted.toString(),
    iv: iv.toString(CryptoJS.enc.Hex)
  };
};

// Decrypt data with the vault key
export const decryptData = (encryptedData, iv, vaultKey) => {
  const decrypted = CryptoJS.AES.decrypt(encryptedData, vaultKey, {
    iv: CryptoJS.enc.Hex.parse(iv),
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  });
  
  return JSON.parse(decrypted.toString(CryptoJS.enc.Utf8));
};

// Generate a random strong password
export const generateRandomPassword = (length = 16) => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+=<>?';
  const randomArray = CryptoJS.lib.WordArray.random(length);
  const result = new Array(length);
  
  const charsLength = chars.length;
  for (let i = 0; i < length; i++) {
    const randomByte = randomArray.words[Math.floor(i / 4)] >> (8 * (i % 4)) & 0xff;
    result[i] = chars[randomByte % charsLength];
  }
  
  return result.join('');
}; 