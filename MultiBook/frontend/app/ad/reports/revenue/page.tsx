'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'

interface RevenueByPeriod {
  period: string
  revenue: number
  order_count: number
  subscription_count: number
  appointment_count: number
  total_count: number
}

interface RevenueByService {
  service_id: number
  service_name: string
  revenue: number
  order_count: number
  subscription_count: number
  appointment_count: number
  total_count: number
}

interface RevenueByStaff {
  staff_id: number
  staff_name: string
  revenue: number
  order_count: number
  subscription_count: number
  appointment_count: number
  total_count: number
}

interface RevenueReport {
  start_date: string
  end_date: string
  period: string
  total_revenue: {
    total_revenue: number
    order_revenue: number
    subscription_revenue: number
    appointment_revenue: number
  }
  by_period?: RevenueByPeriod[]
  by_service?: RevenueByService[]
  by_staff?: RevenueByStaff[]
}

interface RevenueReportResponse {
  success: boolean
  data: RevenueReport
  meta: {
    generated_at: string
    format: string
  }
}

/**
 * Revenue Reports Page
 * Route: /ad/reports/revenue (Security: /ad/)
 */
export default function RevenueReportsPage() {
  const [report, setReport] = useState<RevenueReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState(() => {
    const date = new Date()
    date.setDate(date.getDate() - 30)
    return date.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0]
  })
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day')
  const [groupBy, setGroupBy] = useState<'all' | 'period' | 'service' | 'staff'>('all')

  useEffect(() => {
    fetchReport()
  }, [])

  const fetchReport = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        period: period,
        group_by: groupBy,
        format: 'json',
      })

      const response = await apiClient.get<RevenueReportResponse>(
        `${ADMIN_ENDPOINTS.REPORTS.REVENUE}?${params.toString()}`
      )

      if (response.data.success && response.data.data) {
        setReport(response.data.data)
      } else {
        setError('Failed to load revenue report')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load revenue report')
      console.error('Error fetching revenue report:', err)
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = async () => {
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        period: period,
        group_by: groupBy,
        format: 'csv',
      })

      const response = await apiClient.get(
        `${ADMIN_ENDPOINTS.REPORTS.REVENUE}?${params.toString()}`,
        { responseType: 'blob' }
      )

      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `revenue_report_${startDate}_to_${endDate}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError('Failed to export CSV')
      console.error('Error exporting CSV:', err)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB')
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Revenue Reports</h1>
            <p className="text-muted-foreground">
              View and export revenue reports by period, service, or staff member.
            </p>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Period
                </label>
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value as 'day' | 'week' | 'month')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                >
                  <option value="day">Day</option>
                  <option value="week">Week</option>
                  <option value="month">Month</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Group By
                </label>
                <select
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value as 'all' | 'period' | 'service' | 'staff')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                >
                  <option value="all">All</option>
                  <option value="period">Period</option>
                  <option value="service">Service</option>
                  <option value="staff">Staff</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <Button onClick={fetchReport} disabled={loading} className="min-h-[44px]">
                {loading ? 'Loading...' : 'Generate Report'}
              </Button>
              {report && (
                <Button onClick={exportCSV} variant="outline" className="min-h-[44px]">
                  Export CSV
                </Button>
              )}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading revenue report...</p>
            </div>
          )}

          {report && !loading && (
            <>
              {/* Total Revenue Summary */}
              <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Total Revenue Summary</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(report.total_revenue.total_revenue)}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Order Revenue</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(report.total_revenue.order_revenue)}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Subscription Revenue</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {formatCurrency(report.total_revenue.subscription_revenue)}
                    </p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-1">Appointment Revenue</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {formatCurrency(report.total_revenue.appointment_revenue)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Revenue by Period */}
              {report.by_period && report.by_period.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                  <h2 className="text-xl font-semibold mb-4">Revenue by Period</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4">Period</th>
                          <th className="text-right py-2 px-4">Revenue</th>
                          <th className="text-right py-2 px-4">Orders</th>
                          <th className="text-right py-2 px-4">Subscriptions</th>
                          <th className="text-right py-2 px-4">Appointments</th>
                          <th className="text-right py-2 px-4">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.by_period.map((item, index) => (
                          <tr key={index} className="border-b">
                            <td className="py-2 px-4">{formatDate(item.period)}</td>
                            <td className="text-right py-2 px-4 font-semibold">
                              {formatCurrency(item.revenue)}
                            </td>
                            <td className="text-right py-2 px-4">{item.order_count}</td>
                            <td className="text-right py-2 px-4">{item.subscription_count}</td>
                            <td className="text-right py-2 px-4">{item.appointment_count}</td>
                            <td className="text-right py-2 px-4">{item.total_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Revenue by Service */}
              {report.by_service && report.by_service.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                  <h2 className="text-xl font-semibold mb-4">Revenue by Service</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4">Service</th>
                          <th className="text-right py-2 px-4">Revenue</th>
                          <th className="text-right py-2 px-4">Orders</th>
                          <th className="text-right py-2 px-4">Subscriptions</th>
                          <th className="text-right py-2 px-4">Appointments</th>
                          <th className="text-right py-2 px-4">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.by_service.map((item) => (
                          <tr key={item.service_id} className="border-b">
                            <td className="py-2 px-4">{item.service_name}</td>
                            <td className="text-right py-2 px-4 font-semibold">
                              {formatCurrency(item.revenue)}
                            </td>
                            <td className="text-right py-2 px-4">{item.order_count}</td>
                            <td className="text-right py-2 px-4">{item.subscription_count}</td>
                            <td className="text-right py-2 px-4">{item.appointment_count}</td>
                            <td className="text-right py-2 px-4">{item.total_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Revenue by Staff */}
              {report.by_staff && report.by_staff.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                  <h2 className="text-xl font-semibold mb-4">Revenue by Staff</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-4">Staff</th>
                          <th className="text-right py-2 px-4">Revenue</th>
                          <th className="text-right py-2 px-4">Orders</th>
                          <th className="text-right py-2 px-4">Subscriptions</th>
                          <th className="text-right py-2 px-4">Appointments</th>
                          <th className="text-right py-2 px-4">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.by_staff.map((item) => (
                          <tr key={item.staff_id} className="border-b">
                            <td className="py-2 px-4">{item.staff_name}</td>
                            <td className="text-right py-2 px-4 font-semibold">
                              {formatCurrency(item.revenue)}
                            </td>
                            <td className="text-right py-2 px-4">{item.order_count}</td>
                            <td className="text-right py-2 px-4">{item.subscription_count}</td>
                            <td className="text-right py-2 px-4">{item.appointment_count}</td>
                            <td className="text-right py-2 px-4">{item.total_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
