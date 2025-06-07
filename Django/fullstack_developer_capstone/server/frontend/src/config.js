// Configuration for API endpoints
const config = {
  // Django backend URL - Using nginx proxy for local development
  DJANGO_API_URL: process.env.REACT_APP_DJANGO_API_URL || 'http://localhost',
  
  // API endpoints
  endpoints: {
    login: '/djangoapp/login',
    register: '/djangoapp/register', 
    logout: '/djangoapp/logout',
    getDealers: '/djangoapp/get_dealers',
    getDealersByState: '/djangoapp/get_dealers/',
    getDealerDetails: '/djangoapp/dealer/',
    getDealerReviews: '/djangoapp/reviews/dealer/',
    addReview: '/djangoapp/add_review',
    getCars: '/djangoapp/get_cars'
  }
};

// Helper function to build full URL
export const buildApiUrl = (endpoint) => {
  return config.DJANGO_API_URL + endpoint;
};

export default config; 