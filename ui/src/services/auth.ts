import { api } from '../config/axios';
import {
  User,
  LoginCredentials,
  RegisterData,
  LoginResponse,
  PasswordChangeData,
  MessageResponse
} from '../types/auth';

export const authApi = {
  // Register a new user
  register: async (userData: RegisterData): Promise<User> => {
    const response = await api.post<User>('/api/v1/auth/register', userData);
    return response.data;
  },

  // Login user
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/api/v1/auth/login', credentials);
    return response.data;
  },

  // Logout current user
  logout: async (): Promise<MessageResponse> => {
    const response = await api.post<MessageResponse>('/api/v1/auth/logout');
    return response.data;
  },

  // Get current user info
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },

  // Update user profile
  updateProfile: async (profile: Partial<User>): Promise<User> => {
    const response = await api.put<User>('/api/v1/auth/me', profile);
    return response.data;
  },

  // Change password
  changePassword: async (passwordData: PasswordChangeData): Promise<MessageResponse> => {
    const response = await api.post<MessageResponse>('/api/v1/auth/change-password', passwordData);
    return response.data;
  },

  // Logout from all sessions
  logoutAll: async (): Promise<MessageResponse> => {
    const response = await api.post<MessageResponse>('/api/v1/auth/logout-all');
    return response.data;
  }
};