// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/login`,
  SIGNUP: `${API_BASE_URL}/signup`,
  VERIFY_TOKEN: `${API_BASE_URL}/verify-token`,
  AUTO_EMBED: `${API_BASE_URL}/auto-embed/`,
  DETECT_ANOMALIES: `${API_BASE_URL}/detect-anomalies/`,
  DETECT_ALERTS: `${API_BASE_URL}/detect-alerts/`,
  SEND_SLACK_ALERT: `${API_BASE_URL}/send-slack-alert/`,
  ASK_AI: `${API_BASE_URL}/ask-ai/`,
  ANALYTICS: (endpoint) => `${API_BASE_URL}${endpoint}`,
};

export default API_ENDPOINTS; 