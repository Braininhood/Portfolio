'use client'

/**
 * Customer Calendar Page
 * Route: /cus/calendar (Customer only)
 * 
 * Full calendar view for customer appointments with sync functionality.
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CustomerCalendarWidget } from '@/components/customer/CustomerCalendarWidget'
import { CalendarSyncWidget } from '@/components/calendar/CalendarSyncWidget'
import Link from 'next/link'

export default function CustomerCalendarPage() {
  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold mb-2">Calendar</h1>
                <p className="text-muted-foreground">
                  View and manage your appointments
                </p>
              </div>
              <Link
                href="/cus/bookings"
                className="text-sm text-primary hover:underline"
              >
                View All Bookings →
              </Link>
            </div>
          </div>

          {/* Calendar and Sync Widget */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <CustomerCalendarWidget />
            </div>
            <div>
              <CalendarSyncWidget settingsHref="/cus/calendar/settings" subtitle="Sync your appointments with your calendar" />
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
