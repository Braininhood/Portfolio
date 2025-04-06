import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Get Django's CSRF token
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

// Set the CSRF token for all Axios requests (we'll add this in our components)
if (csrfToken) {
  window.csrfToken = csrfToken;
}

// Extract username from Django template if user is authenticated
try {
  const userElement = document.getElementById('user-data');
  if (userElement) {
    window.user = {
      username: userElement.dataset.username,
    };
  }
} catch (error) {
  console.error('Error extracting user data:', error);
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 