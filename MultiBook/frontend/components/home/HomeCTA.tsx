'use client'

/**
 * Home page CTA: show login state and correct buttons.
 * - Logged in: "Logged in as [name/email]", link to role dashboard, Logout
 * - Not logged in: Book Now, Login, Register
 */
import Link from 'next/link'
import { useAuthContext } from '@/components/auth/AuthProvider'

const ROLE_DASHBOARD: Record<string, string> = {
  customer: '/cus/dashboard',
  staff: '/st/dashboard',
  manager: '/man/dashboard',
  admin: '/ad/dashboard',
}

export function HomeCTA() {
  const { user, isAuthenticated, isLoading, logout } = useAuthContext()

  if (isLoading) {
    return (
      <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
        <span className="text-muted-foreground">Loading...</span>
      </div>
    )
  }

  if (isAuthenticated && user) {
    const displayName = user.first_name || user.email || 'You'
    const dashboardPath = ROLE_DASHBOARD[user.role] || '/cus/dashboard'
    return (
      <div className="space-y-4 mt-8">
        <p className="text-sm text-muted-foreground">
          Logged in as <span className="font-medium text-foreground">{displayName}</span>
          {user.role && (
            <span className="ml-1 text-muted-foreground">({user.role})</span>
          )}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/booking"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center"
          >
            Book Now
          </Link>
          <Link
            href={dashboardPath}
            className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
          >
            My Dashboard
          </Link>
          <button
            type="button"
            onClick={() => logout()}
            className="px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
      <Link
        href="/booking"
        className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center"
      >
        Book Now
      </Link>
      <Link
        href="/login"
        className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
      >
        Login
      </Link>
      <Link
        href="/register"
        className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
      >
        Register
      </Link>
    </div>
  )
}
