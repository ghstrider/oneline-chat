import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../services/auth';
import { User, LoginCredentials, RegisterData } from '../types/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (profile: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionToken, setSessionToken] = useState<string | null>(
    localStorage.getItem('sessionToken')
  );

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('sessionToken');
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token is invalid or expired
          localStorage.removeItem('sessionToken');
          setSessionToken(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await authApi.login(credentials);
      setUser(response.user);
      setSessionToken(response.session_token);
      localStorage.setItem('sessionToken', response.session_token);
      
      // Store expiry for session management
      localStorage.setItem('sessionExpiry', response.expires_at);
    } catch (error) {
      throw error;
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      const newUser = await authApi.register(userData);
      // After registration, automatically log in
      await login({
        username_or_email: userData.username,
        password: userData.password,
        remember_me: false
      });
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (sessionToken) {
        await authApi.logout();
      }
    } catch (error) {
      // Even if logout fails on server, clear local session
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setSessionToken(null);
      localStorage.removeItem('sessionToken');
      localStorage.removeItem('sessionExpiry');
    }
  };

  const updateProfile = async (profile: Partial<User>) => {
    try {
      const updatedUser = await authApi.updateProfile(profile);
      setUser(updatedUser);
    } catch (error) {
      throw error;
    }
  };

  const value: AuthState = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    updateProfile
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};