import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';  // Changed from 8000 to 8000

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const submitAnalysis = async (postUrl) => {
  const response = await api.post('/analyze', { post_url: postUrl });
  return response.data;
};

export const getAnalysis = async (analysisId) => {
  const response = await api.get(`/analysis/${analysisId}`);
  return response.data;
};

export const getRecentAnalyses = async (limit = 10) => {
  const response = await api.get(`/analyses?limit=${limit}`);
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};