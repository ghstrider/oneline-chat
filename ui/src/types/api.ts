import { AxiosError } from 'axios'

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: any
}

export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

export interface StreamError extends Error {
  code?: string
  status?: number
}

// Type guard for axios errors
export const isAxiosError = (error: unknown): error is AxiosError => {
  return error !== null && typeof error === 'object' && 'isAxiosError' in error
}

// Helper to extract error message from various error types
export const getErrorMessage = (error: unknown): string => {
  if (isAxiosError(error)) {
    return error.message || 'Request failed'
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  if (typeof error === 'string') {
    return error
  }
  
  return 'An unknown error occurred'
}

// Helper to extract status code from error
export const getErrorStatus = (error: unknown): number | undefined => {
  if (isAxiosError(error)) {
    return error.response?.status
  }
  
  return undefined
}