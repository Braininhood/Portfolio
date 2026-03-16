/**
 * Authentication Hook
 * 
 * Manages authentication state and provides auth methods.
 */
'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import type { LoginRequest, RegisterRequest, User, UserRole } from '@/types/auth'

export function useAuth() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication status on mount
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsAuthenticated(false)
        setIsLoading(false)
        return
      }

      // Verify token by fetching user profile
      // Backend /api/aut/me/ returns { success, data } where data IS the user object (not data.user)
      try {
        const profileData = await apiClient.getUserProfile()
        const userData = profileData?.user ?? profileData
        if (userData && (userData.id != null || userData.email)) {
          setUser(userData)
          setIsAuthenticated(true)
        } else {
          throw new Error('No user data in profile')
        }
      } catch (error) {
        // Token invalid or expired
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setIsAuthenticated(false)
        setUser(null)
      }
    } catch (error) {
      setIsAuthenticated(false)
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginRequest, expectedRole?: UserRole) => {
    try {
      const response = await apiClient.login(credentials.email, credentials.password)
      setUser(response.user)
      setIsAuthenticated(true)
      
      // If expected role is specified, verify it matches
      if (expectedRole && response.user.role !== expectedRole) {
        throw { error: { code: 'WRONG_ROLE', message: `This login is only for ${expectedRole} users.` } }
      }
      
      const rolePrefix = getRolePrefix(response.user.role)
      router.push(`/${rolePrefix}/dashboard`)
      return response
    } catch (error: any) {
      // Handle error response format from backend
      if (error.response?.data) {
        throw error.response.data
      }
      throw error
    }
  }

  const register = async (data: RegisterRequest) => {
    try {
      const role = data.role || 'customer'
      const registerData: any = {
        email: data.email,
        password: data.password,
        name: data.name || '', // Send name directly - backend will split it
        phone: data.phone || '',
        role: role,
      }
      
      // Include invitation_token if provided (required for staff/manager/admin)
      if (data.invitation_token) {
        registerData.invitation_token = data.invitation_token
      }
      
      const response = await apiClient.register(registerData)
      
      // SECURITY: Check redirect_to_login flag (email already exists)
      // Backend returns 200 OK for both cases to prevent user enumeration
      if (response.redirect_to_login) {
        // Return response with flag - let the component handle redirect
        return response
      }
      
      // After registration, user is automatically logged in
      if (response.user) {
        setUser(response.user)
        setIsAuthenticated(true)
        const rolePrefix = getRolePrefix(response.user.role)
        router.push(`/${rolePrefix}/dashboard`)
      }
      return response
    } catch (error: any) {
      // Handle error response format from backend
      if (error.response?.data) {
        throw error.response.data
      }
      throw error
    }
  }

  const logout = async () => {
    try {
      await apiClient.logout()
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      setUser(null)
      setIsAuthenticated(false)
      router.push('/login')
    }
  }

  const getRolePrefix = (role: UserRole): string => {
    const roleMap: Record<UserRole, string> = {
      customer: 'cus',
      staff: 'st',
      manager: 'man',
      admin: 'ad',
    }
    return roleMap[role] || 'cus'
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
    getRolePrefix,
  }
}
