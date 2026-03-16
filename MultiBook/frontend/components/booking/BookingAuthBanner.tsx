'use client'

/**
 * Banner on booking steps: show whether user is guest or logged in.
 * - Guest: "Guest checkout – no login required"
 * - Logged in (customer): "Logged in as [email] – your details will be pre-filled on the details step"
 * - Logged in (other role): "Logged in as [email]"
 */
import { useAuthContext } from '@/components/auth/AuthProvider'

export function BookingAuthBanner() {
  const { user, isAuthenticated, isLoading } = useAuthContext()

  if (isLoading) return null

  if (isAuthenticated && user?.email) {
    return (
      <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
        <p className="text-sm text-green-800 dark:text-green-200">
          <span className="font-medium">Logged in as {user.email}</span>
          {user.role === 'customer' && (
            <> – your details will be pre-filled on the &quot;Your Details&quot; step.</>
          )}
        </p>
      </div>
    )
  }

  return (
    <div className="mb-6 p-4 bg-muted rounded-lg">
      <p className="text-sm text-muted-foreground">
        <span className="font-medium">Guest checkout</span> – no login required. You can create an account after booking if you like.
      </p>
    </div>
  )
}
