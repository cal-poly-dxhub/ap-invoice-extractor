import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 120000, // 2 minutes for document processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Document processing API
export const documentAPI = {
  // Process a single document
  processDocument: async (fileData) => {
    const response = await api.post('/process-document', fileData);
    return response.data;
  },

  // Process document from S3
  processS3Document: async (s3Key, bucketName = null) => {
    const response = await api.post('/process-s3-document', {
      s3_key: s3Key,
      bucket_name: bucketName,
      document_type: 'invoice'
    });
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

// Chat API
export const chatAPI = {
  // Create a new chat session with invoice data
  createSession: async (invoices) => {
    const response = await api.post('/create-session', {
      invoices: invoices
    });
    return response.data;
  },

  // Send a chat message
  sendMessage: async (sessionId, message) => {
    const response = await api.post('/chat', {
      session_id: sessionId,
      message: message
    });
    return response.data;
  },

  // Get session status
  getSessionStatus: async (sessionId) => {
    const response = await api.get(`/session/${sessionId}/status`);
    return response.data;
  },

  // Delete a session
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/session/${sessionId}`);
    return response.data;
  },

  // Get session statistics
  getSessionStats: async () => {
    const response = await api.get('/sessions/stats');
    return response.data;
  }
};

export default api; 