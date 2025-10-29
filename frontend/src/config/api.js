/**
 * API Configuration
 * Centralized configuration for all API endpoints
 */

// Determine the base URL based on environment
const getBaseURL = () => {
  // Check if we're in development (localhost)
//   if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
//     return 'http://localhost:8000';
//   }
  
  // Production URL
  return 'https://9dgmu9h2pg.us-east-1.awsapprunner.com';
};

export const BASE_URL = getBaseURL();
export const API_BASE_URL = `${BASE_URL}/api`;

export default { BASE_URL, API_BASE_URL };
