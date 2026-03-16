/**
 * Protected Route Component
 * 
 * Protects routes based on authentication and role requirements.
 */
'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthContext } from './AuthProvider'
import type { UserRole } from '@/types/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: UserRole | UserRole[]
  redirectTo?: string
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  redirectTo = '/login'
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user, checkAuth } = useAuthContext()
  const router = useRouter()
  const triedRecheck = useRef(false)

  useEffect(() => {
    // If we have a token but context not hydrated yet, try checkAuth once (e.g. after Google redirect)
    const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('access_token')
    if (!isLoading && !isAuthenticated && !user && hasToken && !triedRecheck.current) {
      triedRecheck.current = true
      checkAuth().then(() => {})
      return
    }

    if (!isLoading) {
      if (!isAuthenticated || !user) {
        router.push(redirectTo)
        return
      }

      if (requiredRole) {
        const allowedRoles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
        if (!allowedRoles.includes(user.role)) {
          const rolePrefix = getRolePrefix(user.role)
          router.push(`/${rolePrefix}/dashboard`)
          return
        }
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRole, router, redirectTo, checkAuth])

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Show nothing while redirecting
  if (!isAuthenticated || !user) {
    return null
  }

  // Check role if required
  if (requiredRole) {
    const allowedRoles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
    if (!allowedRoles.includes(user.role)) {
      return null
    }
  }

  return <>{children}</>
}

function getRolePrefix(role: UserRole): string {
  const roleMap: Record<UserRole, string> = {
    customer: 'cus',
    staff: 'st',
    manager: 'man',
    admin: 'ad',
  }
  return roleMap[role] || 'cus'
}
