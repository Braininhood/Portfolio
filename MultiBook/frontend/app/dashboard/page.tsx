'use client'

/**
 * /dashboard – redirect to role-specific dashboard (same as email login).
 * If authenticated: /cus/dashboard, /ad/dashboard, /st/dashboard, or /man/dashboard.
 * If not: redirect to /login.
 * Handles case where OAuth redirects to /dashboard; we wait for token hydration then redirect.
 */
import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthContext } from '@/components/auth/AuthProvider'

const ROLE_PREFIX: Record<string, string> = {
  admin: 'ad',
  customer: 'cus',
  staff: 'st',
  manager: 'man',
}

export default function DashboardRedirectPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading, user, checkAuth } = useAuthContext()
  const triedAuth = useRef(false)

  useEffect(() => {
    const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('access_token')
    if (hasToken && !user && !isLoading && !triedAuth.current) {
      triedAuth.current = true
      checkAuth().then(() => {})
      return
    }
    if (isLoading) return
    if (isAuthenticated && user?.role) {
      const prefix = ROLE_PREFIX[user.role] ?? 'cus'
      router.replace(`/${prefix}/dashboard`)
    } else {
      router.replace('/login')
    }
  }, [isLoading, isAuthenticated, user, router, checkAuth])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-muted-foreground">Redirecting to dashboard...</p>
    </div>
  )
}
