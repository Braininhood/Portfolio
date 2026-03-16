'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, AppointmentListResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

/**
 * Staff Jobs List Page
 * Route: /st/jobs (Security: /st/)
 */
export default function StaffJobs() {
  const router = useRouter()
  const [jobs, setJobs] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [dateFilter, setDateFilter] = useState<string>('today')

  useEffect(() => {
    fetchJobs()
  }, [statusFilter, dateFilter])

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      
      // Date filter
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      if (dateFilter === 'today') {
        const tomorrow = new Date(today)
        tomorrow.setDate(tomorrow.getDate() + 1)
        params.append('date_from', today.toISOString())
        params.append('date_to', tomorrow.toISOString())
      } else if (dateFilter === 'week') {
        const nextWeek = new Date(today)
        nextWeek.setDate(nextWeek.getDate() + 7)
        params.append('date_from', today.toISOString())
        params.append('date_to', nextWeek.toISOString())
      } else if (dateFilter === 'month') {
        const nextMonth = new Date(today)
        nextMonth.setMonth(nextMonth.getMonth() + 1)
        params.append('date_from', today.toISOString())
        params.append('date_to', nextMonth.toISOString())
      }
      
      // Status filter
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }
      
      const response = await apiClient.get<AppointmentListResponse & { results?: Appointment[] }>(
        `${STAFF_ENDPOINTS.JOBS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      )
      const raw = response.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
      const list = raw.results ?? raw.data ?? []
      if (Array.isArray(list)) {
        const sorted = [...list].sort((a, b) =>
          new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        )
        setJobs(sorted)
      } else {
        setError('Failed to load jobs')
      }
    } catch (err: any) {
      const status = err.response?.status
      const msg = err.response?.data?.error?.message || err.response?.data?.detail
      if (status === 401) {
        setError('Please log in again to view your jobs.')
      } else {
        setError(msg || 'Failed to load jobs')
      }
      console.error('Error fetching jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('en-GB', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
      }),
      time: date.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    }
  }

  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">My Jobs</h1>
            <p className="text-muted-foreground">
              View and manage your assigned jobs
            </p>
          </div>

          {/* Filters */}
          <div className="bg-card border rounded-lg p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Status</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Date Range</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={dateFilter}
                  onChange={(e) => setDateFilter(e.target.value)}
                >
                  <option value="today">Today</option>
                  <option value="week">Next 7 Days</option>
                  <option value="month">Next 30 Days</option>
                </select>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6 flex flex-col gap-2">
              <span>{error}</span>
              {error.includes('log in again') && (
                <Link href="/st/login" className="text-primary font-medium underline">
                  Go to staff login →
                </Link>
              )}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading jobs...</p>
            </div>
          )}

          {/* Jobs List */}
          {!loading && !error && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {jobs.length} job{jobs.length !== 1 ? 's' : ''}
              </div>
              {jobs.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  No jobs found
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => {
                    const { date, time } = formatDateTime(job.start_time)
                    return (
                      <div
                        key={job.id}
                        className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => router.push(`/st/jobs/${job.id}`)}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-semibold">{job.service?.name || 'Service'}</h3>
                              <span className={`px-2 py-1 rounded text-xs ${
                                job.status === 'completed' ? 'bg-green-100 text-green-800' :
                                job.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                job.status === 'confirmed' ? 'bg-yellow-100 text-yellow-800' :
                                job.status === 'pending' ? 'bg-gray-100 text-gray-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {job.status}
                              </span>
                            </div>
                            <div className="text-sm text-muted-foreground space-y-1">
                              <div>{date} at {time}</div>
                              {job.customer_booking?.customer && (
                                <div>
                                  Customer: {job.customer_booking.customer.name}
                                  {job.customer_booking.customer.phone && (
                                    <span className="ml-2">({job.customer_booking.customer.phone})</span>
                                  )}
                                </div>
                              )}
                              {job.location_notes && (
                                <div className="mt-2 text-xs">
                                  📍 {job.location_notes}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium">
                              {job.appointment_type === 'subscription' && '📅 Subscription'}
                              {job.appointment_type === 'order_item' && '📦 Order'}
                              {job.appointment_type === 'single' && '📋 Single'}
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                router.push(`/st/jobs/${job.id}`)
                              }}
                              className="mt-2 text-primary hover:underline text-sm"
                            >
                              View Details →
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
