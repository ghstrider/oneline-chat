// API Configuration
export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  endpoints: {
    chat: '/api/v1/chat/completions',
    stream: '/api/v1/chat/stream',
    history: '/api/v1/chat/history',
    models: '/api/v1/models',
  },
  // Axios-specific configurations
  retries: 3,
  retryDelay: 1000,
  maxRedirects: 5,
}

export const getApiUrl = (endpoint: keyof typeof API_CONFIG.endpoints): string => {
  return `${API_CONFIG.baseUrl}${API_CONFIG.endpoints[endpoint]}`
}

export const getFullUrl = (path: string): string => {
  return `${API_CONFIG.baseUrl}${path}`
}