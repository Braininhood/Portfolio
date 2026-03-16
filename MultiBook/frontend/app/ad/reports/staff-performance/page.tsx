'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'
import { useEffect, useState } from 'react'

interface StaffPerformanceRow {
  staff_id: number
  staff_name: string
  email: string
  jobs_completed: number
  total_appointments: number
  utilization_rate_pct: number
  revenue: number
  order_count: number
  subscription_count: number
  appointment_count: number
  avg_rating: number | null
  rating_count: number
  rank_by_jobs: number
  rank_by_revenue: number
  rank_by_utilization: number
}

interface StaffPerformanceData {
  staff_performance: StaffPerformanceRow[]
  summary: {
    total_staff: number
    total_jobs_completed: number
    total_revenue: number
  }
}

/**
 * Staff Performance Reports Page (Day 5)
 * Route: /ad/reports/staff-performance
 */
export default function StaffPerformancePage() {
  const [data, setData] = useState<StaffPerformanceData | null>(null)
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
      const res = await apiClient.get<{ success: boolean; data: StaffPerformanceData }>(
        `${ADMIN_ENDPOINTS.REPORTS.STAFF_PERFORMANCE}?start_date=${startDate}&end_date=${endDate}`
      )
      if (res.data.success && res.data.data) setData(res.data.data)
      else setError('Failed to load report')
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load staff performance report')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReport()
  }, [])

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(n)

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Staff Performance Reports</h1>
              <p className="text-muted-foreground mt-1">
                Jobs completed, revenue per staff, utilization rate, comparative analytics
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
              {/* Summary */}
              <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-muted-foreground">Total Staff</h3>
                  <p className="text-2xl font-bold">{data.summary.total_staff}</p>
                </div>
                <div className="bg-card border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-muted-foreground">Jobs Completed</h3>
                  <p className="text-2xl font-bold">{data.summary.total_jobs_completed}</p>
                </div>
                <div className="bg-card border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-muted-foreground">Total Revenue</h3>
                  <p className="text-2xl font-bold">{formatCurrency(data.summary.total_revenue)}</p>
                </div>
              </section>

              {/* Performance table */}
              <section className="bg-card border rounded-lg p-6 overflow-x-auto">
                <h2 className="text-xl font-semibold mb-4">Performance by Staff</h2>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Staff</th>
                      <th className="text-right py-2">Jobs</th>
                      <th className="text-right py-2">Utilization %</th>
                      <th className="text-right py-2">Revenue</th>
                      <th className="text-right py-2">Rank (jobs)</th>
                      <th className="text-right py-2">Rank (revenue)</th>
                      <th className="text-right py-2">Rank (util)</th>
                      <th className="text-right py-2">Ratings</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.staff_performance.map((row) => (
                      <tr key={row.staff_id} className="border-b border-border/50 hover:bg-muted/50">
                        <td className="py-2">
                          <div className="font-medium">{row.staff_name}</div>
                          <div className="text-xs text-muted-foreground">{row.email}</div>
                        </td>
                        <td className="text-right py-2">
                          {row.jobs_completed} / {row.total_appointments}
                        </td>
                        <td className="text-right py-2">{row.utilization_rate_pct}%</td>
                        <td className="text-right py-2">{formatCurrency(row.revenue)}</td>
                        <td className="text-right py-2">#{row.rank_by_jobs}</td>
                        <td className="text-right py-2">#{row.rank_by_revenue}</td>
                        <td className="text-right py-2">#{row.rank_by_utilization}</td>
                        <td className="text-right py-2">
                          {row.avg_rating != null
                            ? `${row.avg_rating.toFixed(1)} (${row.rating_count})`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

              {/* Comparative note */}
              <p className="text-sm text-muted-foreground">
                Rankings: #1 = best in period. Utilization = jobs completed / total appointments.
                Customer ratings shown when available.
              </p>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
