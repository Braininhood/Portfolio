'use client'

/**
 * Staff Calendar – week view with jobs (Outlook-style).
 * Same layout and sync widget style as customer calendar.
 * Route: /st/calendar (staff only).
 */
import { Fragment, useEffect, useState } from 'react'
import Link from 'next/link'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CalendarSyncWidget } from '@/components/calendar/CalendarSyncWidget'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment } from '@/types/appointment'

export default function StaffCalendarPage() {
  const [weekStart, setWeekStart] = useState(() => {
    const d = new Date()
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1)
    return new Date(d.getFullYear(), d.getMonth(), diff)
  })
  const [staffJobs, setStaffJobs] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(weekStart.getDate() + i)
    return d
  })
  const hours = Array.from({ length: 15 }, (_, i) => i + 6) // 06:00 - 20:00
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`
  const currentHour = now.getHours()
  const currentDayIndex = weekDays.findIndex(
    (d) => d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  )

  const jobsByDayHour: Record<string, Appointment[]> = {}
  staffJobs.forEach((job) => {
    const d = new Date(job.start_time)
    const dayIdx = weekDays.findIndex(
      (w) => w.getFullYear() === d.getFullYear() && w.getMonth() === d.getMonth() && w.getDate() === d.getDate()
    )
    if (dayIdx < 0) return
    const hour = d.getHours()
    const key = `${dayIdx}-${hour}`
    if (!jobsByDayHour[key]) jobsByDayHour[key] = []
    jobsByDayHour[key].push(job)
  })

  useEffect(() => {
    setLoading(true)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    const dateFrom = weekStart.toISOString().slice(0, 10)
    const dateTo = weekEnd.toISOString().slice(0, 10)
    apiClient
      .get(STAFF_ENDPOINTS.JOBS.LIST, { params: { date_from: dateFrom, date_to: dateTo } })
      .then((res) => {
        const raw = res.data as { results?: Appointment[]; data?: Appointment[]; success?: boolean }
        const list = raw?.results ?? (raw?.success && raw?.data ? raw.data : null)
        setStaffJobs(Array.isArray(list) ? list : [])
      })
      .catch(() => setStaffJobs([]))
      .finally(() => setLoading(false))
  }, [weekStart])

  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold mb-2">Calendar</h1>
                <p className="text-muted-foreground">
                  View and manage your jobs
                </p>
              </div>
              <Link href="/st/jobs" className="text-sm text-primary hover:underline">
                View All Jobs →
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col min-h-[500px]">
              <div className="flex items-center justify-between mb-4 flex-shrink-0">
                <nav className="flex items-center gap-1 text-sm">
                  <button
                    type="button"
                    onClick={() => {
                      const prev = new Date(weekStart)
                      prev.setDate(prev.getDate() - 7)
                      setWeekStart(prev)
                    }}
                    className="p-2 rounded hover:bg-muted"
                    aria-label="Previous week"
                  >
                    ←
                  </button>
                  <span className="min-w-[200px] text-center font-medium">
                    {weekDays[0].toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })} – {weekDays[6].toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      const next = new Date(weekStart)
                      next.setDate(next.getDate() + 7)
                      setWeekStart(next)
                    }}
                    className="p-2 rounded hover:bg-muted"
                    aria-label="Next week"
                  >
                    →
                  </button>
                </nav>
              </div>

              <div className="flex-1 min-h-[300px] max-h-[80vh] rounded-lg border bg-card overflow-x-auto flex flex-col">
            {loading ? (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                Loading…
              </div>
            ) : (
              <div
                className="flex-1 overflow-auto"
                style={{ minHeight: '400px' }}
              >
                <div
                  className="grid gap-0"
                  style={{
                    gridTemplateColumns: '56px repeat(7, minmax(0, 1fr))',
                    gridTemplateRows: `auto repeat(${hours.length}, minmax(48px, 1fr))`,
                  }}
                >
                  <div className="bg-muted/40 border-b border-r border-border sticky top-0 z-10" />
                  {weekDays.map((d, col) => {
                    const isToday = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}` === todayStr
                    return (
                      <div
                        key={col}
                        className={`border-b border-r border-border py-2 px-1 text-center text-sm font-medium sticky top-0 z-10 bg-background ${isToday ? 'bg-primary/10 text-primary' : 'text-muted-foreground'}`}
                      >
                        <div>{['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][col]}</div>
                        <div className={`text-lg ${isToday ? 'font-bold' : ''}`}>{d.getDate()}</div>
                      </div>
                    )
                  })}
                  {hours.map((hour) => (
                    <Fragment key={hour}>
                      <div className="bg-muted/30 border-b border-r border-border text-xs text-muted-foreground py-1 pr-1 text-right sticky left-0 z-10 bg-background">
                        {hour.toString().padStart(2, '0')}:00
                      </div>
                      {weekDays.map((d, col) => {
                        const isToday = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}` === todayStr
                        const key = `${col}-${hour}`
                        const cellJobs = jobsByDayHour[key] || []
                        const isCurrentTime = currentDayIndex === col && currentHour === hour
                        return (
                          <div
                            key={`${hour}-${col}`}
                            className={`border-b border-r border-border min-h-[48px] p-0.5 ${isToday ? 'bg-primary/5' : ''} ${isCurrentTime ? 'relative' : ''}`}
                          >
                            {isCurrentTime && (
                              <div className="absolute left-0 right-0 top-0 h-0.5 bg-red-500 z-20" />
                            )}
                            {cellJobs.map((job) => (
                              <Link
                                key={job.id}
                                href={`/st/jobs/${job.id}`}
                                className="block rounded px-1.5 py-1 text-xs bg-primary/15 text-primary hover:bg-primary/25 truncate border border-primary/30"
                                title={`${job.service?.name || 'Job'} – ${new Date(job.start_time).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`}
                              >
                                {job.service?.name || `#${job.id}`}
                              </Link>
                            ))}
                          </div>
                        )
                      })}
                    </Fragment>
                  ))}
                </div>
              </div>
            )}
              </div>
              <p className="text-xs text-muted-foreground mt-2 flex-shrink-0">
                Click a job to open it. Red line = current time.
              </p>
            </div>
            <div>
              <CalendarSyncWidget settingsHref="/st/calendar/settings" subtitle="Sync your jobs with your calendar" />
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
