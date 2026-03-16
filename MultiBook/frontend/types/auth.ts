/**
 * Authentication and User Types
 */

export type UserRole = 'admin' | 'manager' | 'staff' | 'customer';

export interface User {
  /** Django backend uses number; Supabase uses UUID string */
  id: number | string;
  username?: string;
  email: string;
  role: UserRole;
  first_name?: string;
  last_name?: string;
  name?: string; // Computed from first_name + last_name
  phone?: string;
  avatar?: string;
  is_active?: boolean;
  is_verified?: boolean;
  date_joined?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm?: string;
  name?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  role?: UserRole;
  invitation_token?: string; // Required for staff/manager/admin registration
}

export interface Profile {
  user: User;
  phone?: string;
  avatar?: string;
  timezone: string;
  preferences: Record<string, any>;
  calendar_sync_enabled: boolean;
  calendar_provider: 'google' | 'outlook' | 'apple' | 'none';
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  refreshToken: string | null;
}

export interface ManagerPermissions {
  can_manage_customers: boolean;
  can_manage_staff: boolean;
  can_manage_appointments: boolean;
  can_view_reports: boolean;
  managed_locations?: number[];
  managed_staff?: number[];
  managed_customers?: number[];
  can_manage_all: boolean;
}
