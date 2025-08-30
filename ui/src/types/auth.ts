export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username_or_email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginResponse {
  user: User;
  session_token: string;
  expires_at: string;
}

export interface PasswordChangeData {
  current_password: string;
  new_password: string;
}

export interface MessageResponse {
  message: string;
}