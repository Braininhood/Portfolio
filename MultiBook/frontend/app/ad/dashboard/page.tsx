'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'
import { useEffect, useState } from 'react'

interface DashboardMetrics {
  orders_today: number
  orders_this_week: number
  orders_pending: number
  orders_confirmed_today: number
  appointments_today: number
  total_customers: number
  total_staff: number
  pending_change_requests: number
  revenue_today: {
    total_revenue: number
    order_revenue: number
    subscription_revenue: number
    appointment_revenue: number
  }
  revenue_this_month: {
    total_revenue: number
    order_revenue: number
    subscription_revenue: number
    appointment_revenue: number
  }
}

interface RecentOrder {
  id: number
  order_number: string
  status: string
  total_price: string
  scheduled_date: string | null
  scheduled_time: string | null
  customer_name: string | null
  created_at: string | null
}

interface UpcomingAppointment {
  id: number
  start_time: string | null
  end_time: string | null
  status: string
  service_name: string | null
  staff_name: string | null
}

interface DashboardData {
  metrics: DashboardMetrics
  recent_orders: RecentOrder[]
  upcoming_appointments: UpcomingAppointment[]
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(value)
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

/**
 * Admin Dashboard
 * Route: /ad/dashboard (Security: /ad/)
 */
export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = async () => {
    try {
      setError(null)
      const res = await apiClient.get(ADMIN_ENDPOINTS.REPORTS.DASHBOARD)
      if (res.data.success && res.data.data) setData(res.data.data)
      else setError('Failed to load dashboard')
    } catch (e: unknown) {
      setError((e as { message?: string })?.message ?? 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  // Auto-refresh every 60s (lightweight "real-time" without WebSocket)
  useEffect(() => {
    const interval = setInterval(fetchDashboard, 60_000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !data) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="animate-pulse space-y-6">
              <div className="h-10 w-64 bg-muted rounded" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-24 bg-muted rounded-lg" />
                ))}
              </div>
              <div className="h-64 bg-muted rounded-lg" />
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (error && !data) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="rounded-lg bg-destructive/10 text-destructive p-4">{error}</div>
            <Button className="mt-4" onClick={() => { setLoading(true); fetchDashboard() }}>
              Retry
            </Button>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const metrics = data?.metrics
  const recent_orders = data?.recent_orders ?? []
  const upcoming_appointments = data?.upcoming_appointments ?? []

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => fetchDashboard()}>
                Refresh
              </Button>
            </div>
          </div>

          {/* Quick actions */}
          <div className="mb-8 p-4 rounded-lg border border-border bg-card">
            <h2 className="text-lg font-semibold mb-3">Quick actions</h2>
            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link href="/booking/postcode">New booking</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/ad/customers">Customers</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/ad/orders">Orders</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/ad/reports/revenue">Revenue report</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/ad/staff">Staff</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/ad/services">Services</Link>
              </Button>
            </div>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-8">
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Orders today</p>
              <p className="text-2xl font-bold">{metrics?.orders_today ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Orders this week</p>
              <p className="text-2xl font-bold">{metrics?.orders_this_week ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Appointments today</p>
              <p className="text-2xl font-bold">{metrics?.appointments_today ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Pending orders</p>
              <p className="text-2xl font-bold">{metrics?.orders_pending ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Revenue today</p>
              <p className="text-2xl font-bold">{metrics?.revenue_today ? formatCurrency(metrics.revenue_today.total_revenue) : '—'}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Revenue this month</p>
              <p className="text-2xl font-bold">{metrics?.revenue_this_month ? formatCurrency(metrics.revenue_this_month.total_revenue) : '—'}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Customers</p>
              <p className="text-2xl font-bold">{metrics?.total_customers ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Active staff</p>
              <p className="text-2xl font-bold">{metrics?.total_staff ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Change requests</p>
              <p className="text-2xl font-bold">{metrics?.pending_change_requests ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-border bg-card">
              <p className="text-sm text-muted-foreground">Confirmed today</p>
              <p className="text-2xl font-bold">{metrics?.orders_confirmed_today ?? 0}</p>
            </div>
          </div>

          {/* Recent activity */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="rounded-lg border border-border bg-card overflow-x-auto">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <h2 className="text-lg font-semibold">Recent orders</h2>
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/ad/orders">View all</Link>
                </Button>
              </div>
              <div className="divide-y divide-border max-h-80 overflow-y-auto">
                {recent_orders.length === 0 ? (
                  <p className="p-4 text-muted-foreground text-sm">No recent orders</p>
                ) : (
                  recent_orders.map((o) => (
                    <Link
                      key={o.id}
                      href={`/ad/orders/${o.id}`}
                      className="block p-4 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{o.order_number}</p>
                          <p className="text-sm text-muted-foreground">{o.customer_name ?? 'Guest'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">£{parseFloat(o.total_price).toFixed(2)}</p>
                          <span className="text-xs capitalize text-muted-foreground">{o.status}</span>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {o.scheduled_date ? formatDate(o.scheduled_date) : '—'}
                        {o.scheduled_time ? ` at ${o.scheduled_time.slice(0, 5)}` : ''}
                      </p>
                    </Link>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-card overflow-x-auto">
              <div className="p-4 border-b border-border">
                <h2 className="text-lg font-semibold">Upcoming appointments</h2>
              </div>
              <div className="divide-y divide-border max-h-80 overflow-y-auto">
                {upcoming_appointments.length === 0 ? (
                  <p className="p-4 text-muted-foreground text-sm">No upcoming appointments</p>
                ) : (
                  upcoming_appointments.map((a) => (
                    <div key={a.id} className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{a.service_name ?? 'Service'}</p>
                          <p className="text-sm text-muted-foreground">{a.staff_name ?? '—'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{a.start_time ? formatTime(a.start_time) : '—'}</p>
                          <span className="text-xs capitalize text-muted-foreground">{a.status}</span>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {a.start_time ? formatDate(a.start_time) : '—'}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
