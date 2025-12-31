import axios from 'axios';

// Configure axios base URL - use proxy path for development
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Validate API URL is configured
if (!API_BASE_URL) {
  console.error('VITE_API_URL environment variable is not set');
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
      
      // Handle validation errors (array format)
      if (Array.isArray(error.response.data.detail)) {
        const messages = error.response.data.detail.map(err => err.msg).join(', ');
        return Promise.reject({ detail: messages });
      }
      
      return Promise.reject(error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
      return Promise.reject({ detail: 'Network error - unable to connect to server' });
    } else {
      // Something else happened
      console.error('Error:', error.message);
      return Promise.reject({ detail: error.message });
    }
  }
);

// API methods
export const uploadInvoice = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const createInvoice = async (invoiceData) => {
  const response = await api.post('/invoices', invoiceData);
  return response.data;
};

export const getInvoices = async (status = null, skip = 0, limit = 100) => {
  const params = { skip, limit };
  if (status) params.status = status;
  
  const response = await api.get('/invoices', { params });
  return response.data;
};

export const getInvoice = async (invoiceId) => {
  const response = await api.get(`/invoices/${invoiceId}`);
  return response.data;
};

export const updateInvoice = async (invoiceId, invoiceData) => {
  const response = await api.put(`/invoices/${invoiceId}`, invoiceData);
  return response.data;
};

export const deleteInvoice = async (invoiceId) => {
  const response = await api.delete(`/invoices/${invoiceId}`);
  return response.data;
};

export const getVendors = async (skip = 0, limit = 100) => {
  const response = await api.get('/vendors', { params: { skip, limit } });
  return response.data;
};

export const createVendor = async (vendorData) => {
  const response = await api.post('/vendors', vendorData);
  return response.data;
};

export const exportCSV = async () => {
  const response = await api.get('/export/csv', {
    responseType: 'blob',
  });
  return response;
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;