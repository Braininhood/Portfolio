'use client'

/**
 * Admin Calendar – same week view as staff calendar; shows all appointments
 * with customer name and staff name on each event.
 * Route: /ad/calendar (admin only).
 */
import { Fragment, useEffect, useState } from 'react'
import Link from 'next/link'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { CalendarSyncWidget } from '@/components/calendar/CalendarSyncWidget'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment } from '@/types/appointment'

function getCustomerName(apt: Appointment): string {
  if (apt.customer_booking?.customer?.name) return apt.customer_booking.customer.name
  return 'Guest'
}

function getStaffName(apt: Appointment): string {
  return apt.staff?.name ?? `Staff #${apt.staff_id}`
}

export default function AdminCalendarPage() {
  const [weekStart, setWeekStart] = useState(() => {
    const d = new Date()
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1)
    return new Date(d.getFullYear(), d.getMonth(), diff)
  })
  const [appointments, setAppointments] = useState<Appointment[]>([])
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

  const appointmentsByDayHour: Record<string, Appointment[]> = {}
  appointments.forEach((apt) => {
    const d = new Date(apt.start_time)
    const dayIdx = weekDays.findIndex(
      (w) => w.getFullYear() === d.getFullYear() && w.getMonth() === d.getMonth() && w.getDate() === d.getDate()
    )
    if (dayIdx < 0) return
    const hour = d.getHours()
    const key = `${dayIdx}-${hour}`
    if (!appointmentsByDayHour[key]) appointmentsByDayHour[key] = []
    appointmentsByDayHour[key].push(apt)
  })

  useEffect(() => {
    setLoading(true)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    const dateFrom = weekStart.toISOString().slice(0, 10)
    const dateTo = weekEnd.toISOString().slice(0, 10)
    apiClient
      .get(ADMIN_ENDPOINTS.APPOINTMENTS.LIST, { params: { date_from: dateFrom, date_to: dateTo } })
      .then((res) => {
        const raw = res.data as { data?: Appointment[]; success?: boolean }
        const list = raw?.success && raw?.data ? raw.data : null
        setAppointments(Array.isArray(list) ? list : [])
      })
      .catch(() => setAppointments([]))
      .finally(() => setLoading(false))
  }, [weekStart])

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold mb-2">Calendar</h1>
                <p className="text-muted-foreground">
                  All appointments · customer and staff on each job
                </p>
              </div>
              <Link href="/ad/appointments" className="text-sm text-primary hover:underline">
                View All Appointments →
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
                            const cellApts = appointmentsByDayHour[key] || []
                            const isCurrentTime = currentDayIndex === col && currentHour === hour
                            return (
                              <div
                                key={`${hour}-${col}`}
                                className={`border-b border-r border-border min-h-[48px] p-0.5 ${isToday ? 'bg-primary/5' : ''} ${isCurrentTime ? 'relative' : ''}`}
                              >
                                {isCurrentTime && (
                                  <div className="absolute left-0 right-0 top-0 h-0.5 bg-red-500 z-20" />
                                )}
                                {cellApts.map((apt) => {
                                  const serviceName = apt.service?.name || `#${apt.id}`
                                  const customerName = getCustomerName(apt)
                                  const staffName = getStaffName(apt)
                                  const title = `${serviceName} · ${customerName} · ${staffName} – ${new Date(apt.start_time).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
                                  return (
                                    <Link
                                      key={apt.id}
                                      href={`/ad/appointments/${apt.id}`}
                                      className="block rounded px-1.5 py-1 text-xs bg-primary/15 text-primary hover:bg-primary/25 border border-primary/30"
                                      title={title}
                                    >
                                      <span className="font-medium truncate block">{serviceName}</span>
                                      <span className="text-muted-foreground truncate block">{customerName} · {staffName}</span>
                                    </Link>
                                  )
                                })}
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
                Click an appointment to open it. Red line = current time. Each block shows service, customer, and staff.
              </p>
            </div>
            <div>
              <CalendarSyncWidget
                settingsHref="/settings/calendar"
                subtitle="Sync your calendar with Google, Outlook, or Apple Calendar"
              />
              <div className="mt-6 bg-card border rounded-lg p-4">
                <h3 className="font-semibold mb-2">All appointments</h3>
                <p className="text-sm text-muted-foreground">
                  Same week view as the staff calendar. Each slot shows <strong>service</strong>, <strong>customer</strong>, and <strong>staff</strong>. Use the arrows to change week; click any appointment to view or edit it.
                </p>
                <Link href="/ad/appointments" className="mt-3 inline-block text-sm text-primary hover:underline">
                  View list →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
