'use client'

/**
 * Calendar Sync Settings (admin, manager, customer – staff redirect to /st/calendar/settings).
 * Route: /settings/calendar
 * Same layout and style as role-specific calendar settings pages.
 */
import { Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthContext } from '@/components/auth/AuthProvider'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CalendarSettingsContent } from '@/components/calendar/CalendarSettingsContent'

function getBackForRole(role: string): { backHref: string; backLabel: string } {
  if (role === 'admin') return { backHref: '/ad/dashboard', backLabel: 'Back to Dashboard' }
  if (role === 'manager') return { backHref: '/man/dashboard', backLabel: 'Back to Dashboard' }
  if (role === 'customer') return { backHref: '/cus/calendar', backLabel: 'Back to Calendar' }
  return { backHref: '/dashboard', backLabel: 'Back' }
}

function CalendarSettingsPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user } = useAuthContext()

  useEffect(() => {
    if (user?.role === 'staff') {
      const q = searchParams?.toString()
      router.replace(q ? `/st/calendar/settings?${q}` : '/st/calendar/settings')
    }
  }, [user?.role, router, searchParams])

  if (user?.role === 'staff') {
    return null
  }

  const { backHref, backLabel } = getBackForRole(user?.role ?? '')

  return (
    <ProtectedRoute requiredRole={['admin', 'manager', 'staff', 'customer']}>
      <DashboardLayout>
        <CalendarSettingsContent
          settingsPath="/settings/calendar"
          backHref={backHref}
          backLabel={backLabel}
        />
      </DashboardLayout>
    </ProtectedRoute>
  )
}

export default function CalendarSettingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-muted-foreground">Loading...</p></div>}>
      <CalendarSettingsPageContent />
    </Suspense>
  )
}
