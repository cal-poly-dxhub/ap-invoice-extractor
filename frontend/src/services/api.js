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

  // Update document structured data
  updateDocument: async (documentId, sessionId, structuredData) => {
    const response = await api.post('/update-document', {
      document_id: documentId,
      session_id: sessionId,
      structured_data: structuredData
    });
    return response.data;
  }
};

// Chat API
export const chatAPI = {
  // Note: Session creation is now handled automatically during document processing

  // Send a chat message
  sendMessage: async (sessionId, message) => {
    const response = await api.post('/chat', {
      session_id: sessionId,
      message: message
    });
    return response.data;
  },



  // Delete a session
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/session/${sessionId}/delete`);
    return response.data;
  },


};

export default api; 