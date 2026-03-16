'use client'

/**
 * Staff Calendar Settings – role-specific URL for staff.
 * Route: /st/calendar/settings (same API as /api/calendar/..., scoped to current user by backend).
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CalendarSettingsContent } from '@/components/calendar/CalendarSettingsContent'

export default function StaffCalendarSettingsPage() {
  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <CalendarSettingsContent
          settingsPath="/st/calendar/settings"
          backHref="/st/calendar"
          backLabel="Back to Calendar"
        />
      </DashboardLayout>
    </ProtectedRoute>
  )
}
