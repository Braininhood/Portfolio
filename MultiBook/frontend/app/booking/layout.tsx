'use client'

/**
 * Booking layout: navigation buttons for all booking steps.
 */
import Link from 'next/link'
import { useAuthContext } from '@/components/auth/AuthProvider'

export default function BookingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isAuthenticated, getRolePrefix } = useAuthContext()

  // Get dashboard URL based on user role
  const getDashboardUrl = () => {
    if (!user?.role) return '/cus/dashboard'
    const prefix = getRolePrefix(user.role)
    return `/${prefix}/dashboard`
  }

  return (
    <div className="min-h-screen">
      <div className="container mx-auto p-4 md:p-6">
        {/* Navigation buttons */}
        <div className="flex gap-3 mb-6">
          <Link
            href="/"
            className="flex-1 py-2 px-4 border border-border rounded-lg hover:bg-muted transition-colors text-center text-sm font-medium"
          >
            Home
          </Link>
          {isAuthenticated && user ? (
            <Link
              href={getDashboardUrl()}
              className="flex-1 py-2 px-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center text-sm font-medium"
            >
              Dashboard
            </Link>
          ) : (
            <Link
              href="/login"
              className="flex-1 py-2 px-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center text-sm font-medium"
            >
              Login / Sign in
            </Link>
          )}
        </div>

        {children}
      </div>
    </div>
  )
}
