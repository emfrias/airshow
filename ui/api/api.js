// api/api.js
import axios from 'axios';
import { getAuthToken, removeAuthToken } from '../utils/auth';
import { router } from 'expo-router'; // Assuming expo-router is used for navigation

// Create axios instance
const api = axios.create({
  baseURL: '', // Replace with your API base URL
  timeout: 5000, // Optional timeout
});

// Request interceptor to add auth token to headers
api.interceptors.request.use(
  async (config) => {
    // Skip adding Authorization header for unauthenticated requests
    if (config.headers['Skip-Auth']) {
      return config;
    }

    const token = await getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      // Prevent the request from being sent if there's no token
      console.log('redirecting to login');
      //const router = useRouter();
      router.replace('/login'); // Redirect to the login page
      return Promise.reject({ message: 'No token available' });
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle unauthorized errors
    if (error.response && error.response.status === 401) {
      removeAuthToken(); // Clear the token from storage
      //const router = useRouter();
      router.replace('/login'); // Redirect to the login page
    }
    return Promise.reject(error);
  }
);

export default api;
