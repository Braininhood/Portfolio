'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'

/**
 * Manager Dashboard
 * Route: /man/dashboard (Security: /man/)
 */
export default function ManagerDashboard() {
  return (
    <ProtectedRoute requiredRole={['admin', 'manager']}>
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <h1 className="text-3xl font-bold mb-8">Manager Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to your manager dashboard. Manage appointments, staff, and customers within your scope here.
          </p>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
