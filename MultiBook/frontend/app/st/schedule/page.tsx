'use client'

import Link from 'next/link'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, StaffSchedule, StaffScheduleResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'

/**
 * Staff Schedule Page
 * Route: /st/schedule (Security: /st/)
 */
export default function StaffSchedulePage() {
  const [schedule, setSchedule] = useState<StaffSchedule[]>([])
  const [weekJobs, setWeekJobs] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [jobsLoading, setJobsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSchedule()
  }, [])

  useEffect(() => {
    const now = new Date()
    const day = now.getDay()
    const diff = now.getDate() - day + (day === 0 ? -6 : 1)
    const mon = new Date(now.getFullYear(), now.getMonth(), diff)
    const sun = new Date(mon)
    sun.setDate(sun.getDate() + 6)
    const dateFrom = mon.toISOString().slice(0, 10)
    const dateTo = sun.toISOString().slice(0, 10)
    apiClient
      .get(STAFF_ENDPOINTS.JOBS.LIST, { params: { date_from: dateFrom, date_to: dateTo } })
      .then((res) => {
        const raw = res.data as { results?: Appointment[]; data?: Appointment[]; success?: boolean }
        const list = raw?.results ?? (raw?.success && raw?.data ? raw.data : null)
        setWeekJobs(Array.isArray(list) ? list : [])
      })
      .catch(() => setWeekJobs([]))
      .finally(() => setJobsLoading(false))
  }, [])

  const fetchSchedule = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<StaffScheduleResponse>(STAFF_ENDPOINTS.SCHEDULE)
      const raw = response.data as
        | { success?: boolean; data?: StaffSchedule[]; results?: StaffSchedule[] }
        | StaffSchedule[]
      const list = Array.isArray(raw)
        ? raw
        : raw?.success && raw?.data
          ? raw.data
          : (raw as { results?: StaffSchedule[] })?.results ?? null
      if (list && Array.isArray(list)) {
        setSchedule(list.filter((s: StaffSchedule) => s.is_active !== false))
      } else {
        setError('Failed to load schedule')
      }
    } catch (err: any) {
      const status = err.response?.status
      if (status === 401) {
        setError('Session expired. Please sign in again.')
      } else {
        setError(err.response?.data?.error?.message || 'Failed to load schedule')
      }
      console.error('Error fetching schedule:', err)
    } finally {
      setLoading(false)
    }
  }

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">My Schedule</h1>
            <p className="text-muted-foreground">
              View your weekly work schedule
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
              {error.includes('Session expired') && (
                <div className="mt-2">
                  <Link href="/st/login" className="font-medium underline">
                    Go to staff login →
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading schedule...</p>
            </div>
          )}

          {/* Work this week */}
          {!loading && !error && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">Work this week</h2>
              {jobsLoading ? (
                <p className="text-muted-foreground text-sm">Loading jobs...</p>
              ) : weekJobs.length === 0 ? (
                <div className="bg-card border rounded-lg p-6 text-center text-muted-foreground">
                  No jobs scheduled this week
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {weekJobs.map((job) => {
                    const start = new Date(job.start_time)
                    const dateStr = start.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
                    const timeStr = start.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
                    return (
                      <Link
                        key={job.id}
                        href={`/st/jobs/${job.id}`}
                        className="bg-card border rounded-lg p-4 hover:bg-muted/50 transition-colors block"
                      >
                        <div className="font-medium">{job.service?.name || `Job #${job.id}`}</div>
                        <div className="text-sm text-muted-foreground mt-1">{dateStr} at {timeStr}</div>
                        <div className="text-xs mt-1">
                          <span className={job.status === 'completed' ? 'text-green-600' : job.status === 'in_progress' ? 'text-blue-600' : 'text-muted-foreground'}>
                            {job.status}
                          </span>
                        </div>
                      </Link>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Weekly availability */}
          {!loading && !error && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold mb-4">Weekly availability</h2>
              {schedule.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  No schedule configured
                </div>
              ) : (
                schedule.map((daySchedule) => (
                  <div key={daySchedule.id} className="bg-card border rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-semibold">
                        {daySchedule.day_name || daysOfWeek[daySchedule.day_of_week]}
                      </h2>
                      <div className="text-sm text-muted-foreground">
                        {daySchedule.start_time} - {daySchedule.end_time}
                      </div>
                    </div>
                    
                    {daySchedule.breaks && daySchedule.breaks.length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <div className="text-sm font-medium mb-2">Breaks:</div>
                        <div className="space-y-2">
                          {daySchedule.breaks.map((breakPeriod, idx) => (
                            <div key={idx} className="text-sm text-muted-foreground flex items-center gap-2">
                              <span>⏸</span>
                              <span>{breakPeriod.start} - {breakPeriod.end}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {(!daySchedule.breaks || daySchedule.breaks.length === 0) && (
                      <div className="text-sm text-muted-foreground mt-2">
                        No breaks scheduled
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
