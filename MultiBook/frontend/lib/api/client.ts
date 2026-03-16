/**
 * API Client Configuration
 * 
 * All API calls use security prefixes:
 * - Public: /api/v1/svc/, /api/v1/stf/, /api/v1/bkg/, /api/v1/addr/, /api/v1/aut/, /api/v1/slots/, /api/v1/pay/
 * - Protected: /api/v1/cus/, /api/v1/st/, /api/v1/man/, /api/v1/ad/
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/`, // No version prefix - using /api/ directly
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // For CORS with credentials
    });

    // Request interceptor - Add JWT token if available; allow FormData to set Content-Type (multipart)
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
          delete config.headers['Content-Type'];
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - Token expired (skip if this was the refresh request itself)
        const isRefreshRequest = originalRequest.url?.includes('/aut/token/refresh/');
        if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.getRefreshToken();
            if (refreshToken) {
              const response = await axios.post(
                `${API_URL}/aut/token/refresh/`,
                { refresh: refreshToken },
                { headers: { 'Content-Type': 'application/json' } }
              );

              const access = response.data.access || response.data.data?.access;
              if (access) {
                this.setToken(access);
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return this.client(originalRequest);
              }
            }
          } catch (refreshError: any) {
            // Only clear and redirect when refresh actually returned 401/403 (token invalid)
            const status = refreshError.response?.status;
            if (status === 401 || status === 403) {
              this.clearTokens();
              if (typeof window !== 'undefined') {
                window.location.href = '/login?message=' + encodeURIComponent('Session expired. Please sign in again.');
              }
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Token management
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  private setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  private clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  // Public API methods (no authentication required)
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  /** POST multipart/form-data (e.g. file upload). Content-Type is cleared in interceptor so browser sets boundary. */
  async postFormData<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, formData, config);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  // Authentication methods
  async login(email: string, password: string) {
    const response = await this.post('/aut/login/', { email, password });
    // Backend returns: { success: true, data: { user: {...}, tokens: { access, refresh } } }
    if (response.data.success && response.data.data) {
      const { user, tokens } = response.data.data;
      if (tokens && typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
      }
      return { user, tokens };
    }
    throw new Error('Invalid login response');
  }

  async googleOAuthStart() {
    const response = await this.get('/aut/google/start/');
    if (response.data.success && response.data.data) {
      return response.data.data.authorization_url;
    }
    throw new Error(response.data?.error?.message || 'Failed to start Google OAuth');
  }

  async googleLogin(accessToken: string, email?: string, name?: string) {
    const body: { access_token: string; email?: string; name?: string } = { access_token: accessToken };
    if (email) body.email = email;
    if (name) body.name = name;
    const response = await this.post('/aut/google/', body);
    if (response.data.success && response.data.data) {
      const { user, tokens } = response.data.data;
      if (tokens && typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
      }
      return { user, tokens };
    }
    throw new Error(response.data?.error?.message || 'Google sign-in failed');
  }

  async register(data: any) {
    const response = await this.post('/aut/register/', data);
    // Backend returns (SECURITY: 200 OK for both existing and new emails):
    // - Existing email: { success: true, data: { redirect_to_login: true, email: ... } }
    // - New user: { success: true, data: { user: {...}, tokens: {...}, redirect_to_login: false } }
    if (response.data.success && response.data.data) {
      const { user, tokens, redirect_to_login, email } = response.data.data;
      
      // Only save tokens if user was actually created (not redirect case)
      if (tokens && typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
      }
      
      // Return full response data so frontend can check redirect_to_login flag
      return { 
        user, 
        tokens, 
        redirect_to_login: redirect_to_login || false,
        email: email || data.email,
        data: response.data.data  // Include full data for frontend
      };
    }
    throw new Error('Invalid registration response');
  }

  async getUserProfile() {
    const response = await this.get('/aut/me/');
    // Backend returns: { success: true, data: <user object> } (data is UserSerializer.data)
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error('Failed to fetch user profile');
  }

  async logout() {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await this.post('/aut/logout/', { refresh: refreshToken });
      }
    } catch (_error) {
      // Continue with logout even if API call fails
    } finally {
      this.clearTokens();
    }
  }

  // Invitation methods
  async validateInvitation(token: string) {
    const response = await this.get(`/aut/invitations/validate/${token}/`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error('Invalid invitation response');
  }

  // Password reset methods
  async requestPasswordReset(email: string) {
    const response = await this.post('/aut/password-reset/request/', { email });
    if (response.data.success) {
      return response.data.data || response.data;
    }
    throw new Error('Password reset request failed');
  }

  async confirmPasswordReset(token: string, code: string, newPassword: string, newPasswordConfirm: string) {
    const response = await this.post('/aut/password-reset/confirm/', {
      token,
      code,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
    if (response.data.success) {
      return response.data.data || response.data;
    }
    throw new Error('Password reset confirmation failed');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export types
export type ApiResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp?: string;
    version?: string;
  };
};
