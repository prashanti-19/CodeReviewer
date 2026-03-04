// API Configuration
// Connected to local backend at http://localhost:8000
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Set to false to use the real backend
export const USE_MOCK_DATA = false;

export const API_ENDPOINTS = {
  ANALYZE: '/analyze',
  JOB_STATUS: '/job',
  JOB_RESULTS: '/job',
} as const;