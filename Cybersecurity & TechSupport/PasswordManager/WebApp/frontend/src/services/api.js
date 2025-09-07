import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to Authorization header if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Authentication API
export const authAPI = {
  register: (username, email, password) => {
    return apiClient.post('/register/', { username, email, password });
  },
  
  login: (username, password) => {
    return apiClient.post('/login/', { username, password });
  },
  
  checkUsername: (username) => {
    return apiClient.post('/check-username/', { username });
  },
  
  setupMasterKey: (salt, verificationHash) => {
    return apiClient.post('/setup-master-key/', { salt, verification_hash: verificationHash });
  },
  
  getMasterKeySalt: () => {
    return apiClient.get('/get-master-key-salt/');
  },
  
  verifyMasterKey: (verificationHash) => {
    return apiClient.post('/verify-master-key/', { verification_hash: verificationHash });
  }
};

// Vault API
export const vaultAPI = {
  getVault: () => {
    return apiClient.get('/vault/');
  },
  
  createVault: (vaultKeyEncrypted, vaultSalt) => {
    return apiClient.post('/vault/', { 
      vault_key_encrypted: vaultKeyEncrypted, 
      vault_salt: vaultSalt 
    });
  },
  
  updateVault: (id, vaultKeyEncrypted, vaultSalt) => {
    return apiClient.put(`/vault/${id}/`, { 
      vault_key_encrypted: vaultKeyEncrypted, 
      vault_salt: vaultSalt 
    });
  }
};

// Password Entries API
export const passwordEntriesAPI = {
  getEntries: () => {
    return apiClient.get('/password-entries/');
  },
  
  createEntry: (encryptedData, iv) => {
    return apiClient.post('/password-entries/', { 
      encrypted_data: encryptedData, 
      iv: iv 
    });
  },
  
  updateEntry: (id, encryptedData, iv) => {
    return apiClient.put(`/password-entries/${id}/`, { 
      encrypted_data: encryptedData, 
      iv: iv 
    });
  },
  
  deleteEntry: (id) => {
    return apiClient.delete(`/password-entries/${id}/`);
  }
}; 