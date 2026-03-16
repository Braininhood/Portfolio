/**
 * Role-Based Route Component
 * 
 * Renders different content based on user role.
 */
'use client'

import { useAuthContext } from './AuthProvider'
import type { UserRole } from '@/types/auth'

interface RoleBasedRouteProps {
  children: React.ReactNode
  allowedRoles: UserRole | UserRole[]
  fallback?: React.ReactNode
}

export function RoleBasedRoute({ 
  children, 
  allowedRoles,
  fallback = null
}: RoleBasedRouteProps) {
  const { user, isAuthenticated } = useAuthContext()

  if (!isAuthenticated || !user) {
    return <>{fallback}</>
  }

  const allowedRolesArray = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles]
  
  if (allowedRolesArray.includes(user.role)) {
    return <>{children}</>
  }

  return <>{fallback}</>
}
