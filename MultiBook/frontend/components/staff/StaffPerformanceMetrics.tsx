'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { Button } from '@/components/ui/button'

interface StaffPerformanceMetricsProps {
  staffId: number
}

interface PerformanceData {
  staff_id: number
  staff_name: string
  period_days: number
  period_start: string
  metrics: {
    jobs_completed: number
    total_appointments: number
    upcoming_appointments: number
    cancelled_appointments: number
    no_shows: number
    completion_rate: number
    no_show_rate: number
    revenue: number
    avg_response_time_hours: number | null
  }
  services_breakdown: Array<{
    service__name: string
    count: number
    revenue: number
  }>
}

export function StaffPerformanceMetrics({ staffId }: StaffPerformanceMetricsProps) {
  const [data, setData] = useState<PerformanceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [periodDays, setPeriodDays] = useState(30)

  useEffect(() => {
    fetchMetrics()
  }, [staffId, periodDays])

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get(
        `${ADMIN_ENDPOINTS.STAFF.PERFORMANCE(staffId)}?days=${periodDays}`
      )
      
      if (response.data.success && response.data.data) {
        setData(response.data.data)
      } else {
        setError('Failed to load performance metrics')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load performance metrics')
      console.error('Error fetching performance metrics:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-2 text-sm text-muted-foreground">Loading performance metrics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 text-destructive rounded-md">
        {error}
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Performance Metrics</h3>
          <p className="text-sm text-muted-foreground">
            Performance data for the last {periodDays} days
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={periodDays === 7 ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPeriodDays(7)}
          >
            7 Days
          </Button>
          <Button
            variant={periodDays === 30 ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPeriodDays(30)}
          >
            30 Days
          </Button>
          <Button
            variant={periodDays === 90 ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPeriodDays(90)}
          >
            90 Days
          </Button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Jobs Completed</div>
          <div className="text-2xl font-bold">{data.metrics.jobs_completed}</div>
          <div className="text-xs text-muted-foreground mt-1">
            of {data.metrics.total_appointments} total
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Completion Rate</div>
          <div className="text-2xl font-bold">{data.metrics.completion_rate}%</div>
          <div className="text-xs text-muted-foreground mt-1">
            Success rate
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Revenue</div>
          <div className="text-2xl font-bold">£{data.metrics.revenue.toFixed(2)}</div>
          <div className="text-xs text-muted-foreground mt-1">
            From completed jobs
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Upcoming</div>
          <div className="text-2xl font-bold">{data.metrics.upcoming_appointments}</div>
          <div className="text-xs text-muted-foreground mt-1">
            Scheduled appointments
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Cancelled</div>
          <div className="text-xl font-semibold">{data.metrics.cancelled_appointments}</div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">No Shows</div>
          <div className="text-xl font-semibold">{data.metrics.no_shows}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {data.metrics.no_show_rate}% rate
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Avg Response Time</div>
          <div className="text-xl font-semibold">
            {data.metrics.avg_response_time_hours !== null
              ? `${data.metrics.avg_response_time_hours.toFixed(1)}h`
              : 'N/A'}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            To confirmation
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <div className="text-sm text-muted-foreground mb-1">Total Appointments</div>
          <div className="text-xl font-semibold">{data.metrics.total_appointments}</div>
        </div>
      </div>

      {/* Services Breakdown */}
      {data.services_breakdown.length > 0 && (
        <div>
          <h4 className="text-md font-semibold mb-3">Services Breakdown</h4>
          <div className="border rounded-lg overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 text-sm font-medium">Service</th>
                  <th className="text-right p-3 text-sm font-medium">Jobs</th>
                  <th className="text-right p-3 text-sm font-medium">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.services_breakdown.map((service, index) => (
                  <tr key={index} className="border-t">
                    <td className="p-3">{service.service__name}</td>
                    <td className="p-3 text-right">{service.count}</td>
                    <td className="p-3 text-right font-medium">£{service.revenue.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
