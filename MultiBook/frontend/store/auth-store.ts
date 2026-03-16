/**
 * Authentication Store (Zustand)
 * 
 * Global state management for authentication.
 */
'use client'

import { create } from 'zustand'
// Note: persist middleware will be added when zustand/middleware is available
// For now, using localStorage directly in the hook
import type { User, AuthState } from '@/types/auth'

interface AuthStore extends AuthState {
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setRefreshToken: (refreshToken: string | null) => void
  clearAuth: () => void
}

// Note: Using basic Zustand store (persist middleware will be added when needed)
export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  token: null,
  refreshToken: null,

  setUser: (user) =>
    set({
      user,
      isAuthenticated: !!user,
    }),

  setToken: (token) =>
    set({
      token,
      isAuthenticated: !!token,
    }),

  setRefreshToken: (refreshToken) =>
    set({ refreshToken }),

  clearAuth: () =>
    set({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
    }),
}))
