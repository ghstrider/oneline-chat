import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { API_CONFIG } from './api'

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: API_CONFIG.baseUrl,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add timestamp to requests for debugging
    const timestamp = new Date().toISOString()
    console.log(`[API Request ${timestamp}]`, {
      method: config.method?.toUpperCase(),
      url: config.url,
      data: config.data,
    })
    
    return config
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses
    const timestamp = new Date().toISOString()
    console.log(`[API Response ${timestamp}]`, {
      status: response.status,
      url: response.config.url,
      data: response.data,
    })
    
    return response
  },
  (error: AxiosError) => {
    // Enhanced error handling
    const timestamp = new Date().toISOString()
    
    if (error.response) {
      // Server responded with error status
      console.error(`[API Error ${timestamp}]`, {
        status: error.response.status,
        statusText: error.response.statusText,
        url: error.config?.url,
        data: error.response.data,
      })
      
      // Custom error messages based on status codes
      switch (error.response.status) {
        case 400:
          error.message = 'Bad Request: Please check your input'
          break
        case 401:
          error.message = 'Unauthorized: Please check your credentials'
          break
        case 403:
          error.message = 'Forbidden: You do not have permission'
          break
        case 404:
          error.message = 'Not Found: The requested resource was not found'
          break
        case 429:
          error.message = 'Too Many Requests: Please slow down'
          break
        case 500:
          error.message = 'Internal Server Error: Something went wrong on the server'
          break
        case 502:
          error.message = 'Bad Gateway: Server is temporarily unavailable'
          break
        case 503:
          error.message = 'Service Unavailable: Server is temporarily down'
          break
        default:
          error.message = `Request failed with status ${error.response.status}`
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error(`[API Network Error ${timestamp}]`, error.request)
      error.message = 'Network Error: Unable to reach the server. Please check your connection.'
    } else {
      // Something else happened
      console.error(`[API Setup Error ${timestamp}]`, error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient