'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'
import { useEffect, useState } from 'react'

interface AppointmentReportsData {
  appointment_statistics: {
    by_status: { status: string; count: number }[]
    total: number
    period_start: string
    period_end: string
  }
  booking_trends: { date: string | null; count: number }[]
  popular_services: { service_id: number; service_name: string; count: number }[]
  peak_times: {
    by_hour: { hour: number; count: number }[]
    by_day_of_week: { day_of_week: number; day_name: string; count: number }[]
  }
  cancellation_rates: {
    cancelled_count: number
    total_count: number
    cancellation_rate_pct: number
  }
  conversion_metrics: {
    completed_count: number
    completed_rate_pct: number
    no_show_count: number
    no_show_rate_pct: number
    confirmed_or_pending_count: number
  }
}

/**
 * Appointment Reports Page (Day 3-4)
 * Route: /ad/reports/appointments
 */
export default function AppointmentReportsPage() {
  const [data, setData] = useState<AppointmentReportsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0])

  const fetchReport = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.get<{ success: boolean; data: AppointmentReportsData }>(
        `${ADMIN_ENDPOINTS.REPORTS.APPOINTMENTS}?start_date=${startDate}&end_date=${endDate}`
      )
      if (res.data.success && res.data.data) setData(res.data.data)
      else setError('Failed to load report')
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load appointment report')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReport()
  }, [])

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Appointment Reports</h1>
              <p className="text-muted-foreground mt-1">
                Statistics, booking trends, popular services, peak times, cancellation & conversion
              </p>
            </div>
            <Link href="/ad/dashboard" className="text-primary hover:underline">
              ← Dashboard
            </Link>
          </div>

          <div className="mb-6 flex flex-wrap gap-4">
            <label className="flex items-center gap-2">
              <span className="text-sm font-medium">Start</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border rounded px-2 py-1"
              />
            </label>
            <label className="flex items-center gap-2">
              <span className="text-sm font-medium">End</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border rounded px-2 py-1"
              />
            </label>
            <button
              onClick={fetchReport}
              disabled={loading}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Apply'}
            </button>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          {loading && !data && (
            <div className="text-center py-12 text-muted-foreground">Loading report...</div>
          )}

          {data && !loading && (
            <div className="space-y-8">
              {/* Appointment statistics */}
              <section className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Appointment Statistics</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Total: {data.appointment_statistics.total} appointments
                </p>
                <div className="flex flex-wrap gap-4">
                  {data.appointment_statistics.by_status.map((s) => (
                    <div key={s.status} className="px-4 py-2 bg-muted rounded">
                      <span className="font-medium capitalize">{s.status}</span>: {s.count}
                    </div>
                  ))}
                </div>
              </section>

              {/* Cancellation & conversion */}
              <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Cancellation Rates</h2>
                  <p className="text-2xl font-bold">{data.cancellation_rates.cancellation_rate_pct}%</p>
                  <p className="text-sm text-muted-foreground">
                    {data.cancellation_rates.cancelled_count} cancelled / {data.cancellation_rates.total_count} total
                  </p>
                </div>
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Conversion Metrics</h2>
                  <p className="text-lg">Completed: {data.conversion_metrics.completed_count} ({data.conversion_metrics.completed_rate_pct}%)</p>
                  <p className="text-sm text-muted-foreground">
                    No-show: {data.conversion_metrics.no_show_count} ({data.conversion_metrics.no_show_rate_pct}%)
                  </p>
                  <p className="text-sm">Confirmed/Pending: {data.conversion_metrics.confirmed_or_pending_count}</p>
                </div>
              </section>

              {/* Popular services */}
              <section className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Popular Services</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Service</th>
                        <th className="text-right py-2">Appointments</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.popular_services.slice(0, 15).map((s) => (
                        <tr key={s.service_id} className="border-b border-border/50">
                          <td className="py-2">{s.service_name}</td>
                          <td className="text-right py-2">{s.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Peak times */}
              <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Peak Times by Hour</h2>
                  <div className="flex flex-wrap gap-1">
                    {data.peak_times.by_hour.map((h) => (
                      <div
                        key={h.hour}
                        className="text-xs px-1 py-0.5 rounded bg-muted"
                        title={`${h.hour}:00 - ${h.count} appointments`}
                      >
                        {h.hour}h:{h.count}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">By Day of Week</h2>
                  <ul className="space-y-2">
                    {data.peak_times.by_day_of_week.map((d) => (
                      <li key={d.day_of_week} className="flex justify-between text-sm">
                        <span>{d.day_name}</span>
                        <span>{d.count}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              {/* Booking trends (summary) */}
              <section className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Booking Trends</h2>
                <p className="text-sm text-muted-foreground mb-2">
                  {data.booking_trends.length} days with data
                </p>
                <div className="h-48 overflow-x-auto flex items-end gap-0.5">
                  {data.booking_trends.slice(-60).map((t, i) => (
                    <div
                      key={i}
                      className="flex-1 min-w-[4px] bg-primary/70 rounded-t hover:bg-primary"
                      style={{ height: `${Math.max(4, (t.count / Math.max(1, Math.max(...data.booking_trends.map((x) => x.count))) * 100))}%` }}
                      title={`${t.date}: ${t.count}`}
                    />
                  ))}
                </div>
              </section>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
