'use client'

/**
 * Customer Calendar Settings
 * Route: /cus/calendar/settings
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CalendarSettingsContent } from '@/components/calendar/CalendarSettingsContent'

export default function CustomerCalendarSettingsPage() {
  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <CalendarSettingsContent
          settingsPath="/cus/calendar/settings"
          backHref="/cus/calendar"
          backLabel="Back to Calendar"
        />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
