'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { TodaySchedule } from '@/components/staff/TodaySchedule'
import { CalendarSyncWidget } from '@/components/staff/CalendarSyncWidget'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, AppointmentListResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

/**
 * Staff Dashboard
 * Route: /st/dashboard (Security: /st/)
 */
export default function StaffDashboard() {
  const router = useRouter()
  const [todayJobs, setTodayJobs] = useState<Appointment[]>([])
  const [upcomingJobs, setUpcomingJobs] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    todayCount: 0,
    upcomingCount: 0,
    completedToday: 0,
    inProgress: 0,
  })

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const tomorrow = new Date(today)
      tomorrow.setDate(tomorrow.getDate() + 1)
      
      // Fetch today's jobs
      const todayParams = new URLSearchParams({
        date_from: today.toISOString(),
        date_to: tomorrow.toISOString(),
      })
      
      const todayResponse = await apiClient.get<AppointmentListResponse & { results?: Appointment[] }>(
        `${STAFF_ENDPOINTS.JOBS.LIST}?${todayParams.toString()}`
      )
      const todayRaw = todayResponse.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
      const todayList = todayRaw.results ?? todayRaw.data ?? []
      if (Array.isArray(todayList)) {
        const allToday = todayList
        setTodayJobs(allToday.filter(job => 
          new Date(job.start_time) >= today && 
          new Date(job.start_time) < tomorrow
        ))
        
        // Calculate stats
        const completedToday = allToday.filter(job => job.status === 'completed').length
        const inProgress = allToday.filter(job => job.status === 'in_progress').length
        
        setStats({
          todayCount: allToday.length,
          upcomingCount: 0, // Will be calculated below
          completedToday,
          inProgress,
        })
      }
      
      // Fetch upcoming jobs (next 7 days)
      const nextWeek = new Date(today)
      nextWeek.setDate(nextWeek.getDate() + 7)
      const upcomingParams = new URLSearchParams({
        date_from: tomorrow.toISOString(),
        date_to: nextWeek.toISOString(),
        status: 'confirmed', // Staff only see confirmed appointments
      })
      
      const upcomingResponse = await apiClient.get<AppointmentListResponse & { results?: Appointment[] }>(
        `${STAFF_ENDPOINTS.JOBS.LIST}?${upcomingParams.toString()}`
      )
      const upcomingRaw = upcomingResponse.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
      const upcomingList = upcomingRaw.results ?? upcomingRaw.data ?? []
      if (Array.isArray(upcomingList)) {
        setUpcomingJobs(upcomingList.slice(0, 5)) // Next 5
        setStats(prev => ({
          ...prev,
          upcomingCount: upcomingList.length,
        }))
      }
    } catch (err: any) {
      const status = err.response?.status
      const msg = err.response?.data?.error?.message || err.response?.data?.detail
      if (status === 401) {
        setError('Please log in again to view your jobs. Use the staff login link if you were signed in elsewhere.')
      } else {
        setError(msg || 'Failed to load jobs')
      }
      console.error('Error fetching jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  }

  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Staff Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here&apos;s your schedule and job overview.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Today&apos;s Jobs</div>
              <div className="text-2xl font-bold">{stats.todayCount}</div>
            </div>
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">In Progress</div>
              <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
            </div>
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Completed Today</div>
              <div className="text-2xl font-bold text-green-600">{stats.completedToday}</div>
            </div>
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Upcoming (7 days)</div>
              <div className="text-2xl font-bold">{stats.upcomingCount}</div>
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

          {/* Today's Schedule & Calendar Sync */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold">Today&apos;s Schedule</h2>
                <Link href="/st/schedule" className="text-primary hover:underline text-sm">
                  View Full Schedule →
                </Link>
              </div>
              <TodaySchedule />
            </div>
            <div>
              <h2 className="text-2xl font-semibold mb-4">Calendar</h2>
              <CalendarSyncWidget />
            </div>
          </div>

          {/* Today's Jobs */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">Today&apos;s Jobs</h2>
              <Link href="/st/jobs" className="text-primary hover:underline text-sm">
                View All Jobs →
              </Link>
            </div>
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : todayJobs.length > 0 ? (
              <div className="bg-card border rounded-lg overflow-x-auto">
                <div className="divide-y divide-border">
                  {todayJobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-4 hover:bg-muted/50 cursor-pointer"
                      onClick={() => router.push(`/st/jobs/${job.id}`)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-medium">{job.service?.name || 'Service'}</div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {formatTime(job.start_time)} - {formatTime(job.end_time)}
                          </div>
                          {job.customer_booking?.customer && (
                            <div className="text-sm text-muted-foreground mt-1">
                              Customer: {job.customer_booking.customer.name}
                            </div>
                          )}
                        </div>
                        <div>
                          <span className={`px-2 py-1 rounded text-xs ${
                            job.status === 'completed' ? 'bg-green-100 text-green-800' :
                            job.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                            job.status === 'confirmed' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {job.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-card border rounded-lg p-8 text-center text-muted-foreground">
                No jobs scheduled for today
              </div>
            )}
          </div>

          {/* Upcoming Jobs */}
          {upcomingJobs.length > 0 && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold">Upcoming Jobs</h2>
                <Link href="/st/jobs" className="text-primary hover:underline text-sm">
                  View All →
                </Link>
              </div>
              <div className="bg-card border rounded-lg overflow-x-auto">
                <div className="divide-y divide-border">
                  {upcomingJobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-4 hover:bg-muted/50 cursor-pointer"
                      onClick={() => router.push(`/st/jobs/${job.id}`)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-medium">{job.service?.name || 'Service'}</div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {formatDate(job.start_time)} at {formatTime(job.start_time)}
                          </div>
                          {job.customer_booking?.customer && (
                            <div className="text-sm text-muted-foreground mt-1">
                              {job.customer_booking.customer.name}
                            </div>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          job.status === 'confirmed' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {job.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
