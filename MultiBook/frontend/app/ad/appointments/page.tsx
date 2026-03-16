'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { formatStatus } from '@/lib/utils'
import Link from 'next/link'
import { useEffect, useState } from 'react'

interface Appointment {
  id: number
  order_number?: string | null
  subscription_number?: string | null
  staff: {
    id: number
    name: string
  }
  service: {
    id: number
    name: string
  }
  start_time: string
  end_time: string
  status: string
  customer_booking?: {
    customer: {
      id: number
      name: string
      email: string
    }
  } | null
}

/**
 * Admin Appointments List
 * Route: /ad/appointments (Security: /ad/)
 */
export default function AdminAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    fetchAppointments()
  }, [statusFilter])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (statusFilter) {
        params.append('status', statusFilter)
      }
      // Get upcoming appointments by default
      const today = new Date().toISOString().split('T')[0]
      params.append('date_from', today)
      
      const url = `${ADMIN_ENDPOINTS.APPOINTMENTS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const res = await apiClient.get(url)
      
      if (res.data.success && Array.isArray(res.data.data)) {
        setAppointments(res.data.data)
      } else {
        setError('Failed to load appointments')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to load appointments')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'confirmed':
        return 'bg-blue-100 text-blue-800'
      case 'in_progress':
        return 'bg-purple-100 text-purple-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'cancelled':
        return 'bg-red-100 text-red-800'
      case 'no_show':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getCustomerName = (appointment: Appointment) => {
    if (appointment.customer_booking?.customer) {
      return appointment.customer_booking.customer.name
    }
    return 'Guest'
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold">Appointments</h1>
            <Button asChild variant="outline">
              <Link href="/ad/dashboard">Dashboard</Link>
            </Button>
          </div>

          {/* Status Filters */}
          <div className="mb-6 flex gap-2 flex-wrap">
            <Button
              variant={statusFilter === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter(null)}
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('pending')}
            >
              Pending
            </Button>
            <Button
              variant={statusFilter === 'confirmed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('confirmed')}
            >
              Confirmed
            </Button>
            <Button
              variant={statusFilter === 'in_progress' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('in_progress')}
            >
              In Progress
            </Button>
            <Button
              variant={statusFilter === 'completed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('completed')}
            >
              Completed
            </Button>
            <Button
              variant={statusFilter === 'cancelled' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('cancelled')}
            >
              Cancelled
            </Button>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">{error}</div>
          )}

          {loading ? (
            <div className="animate-pulse space-y-2">Loading…</div>
          ) : (
            <div className="rounded-lg border border-border overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-3 font-medium">Date & Time</th>
                    <th className="p-3 font-medium">Service</th>
                    <th className="p-3 font-medium">Staff</th>
                    <th className="p-3 font-medium">Customer</th>
                    <th className="p-3 font-medium">Status</th>
                    <th className="p-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {appointments.map((apt) => (
                    <tr key={apt.id} className="hover:bg-muted/50">
                      <td className="p-3">
                        {new Date(apt.start_time).toLocaleString('en-GB', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td className="p-3">{apt.service.name}</td>
                      <td className="p-3">{apt.staff.name}</td>
                      <td className="p-3">{getCustomerName(apt)}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(apt.status)}`}>
                          {formatStatus(apt.status)}
                        </span>
                      </td>
                      <td className="p-3">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/ad/appointments/${apt.id}`}>Manage</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {appointments.length === 0 && (
                <p className="p-6 text-center text-muted-foreground">No appointments found</p>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
