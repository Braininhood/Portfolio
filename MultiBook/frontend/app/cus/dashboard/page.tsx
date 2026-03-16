'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS, PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment } from '@/types/appointment'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

/**
 * Customer Dashboard
 * Route: /cus/dashboard (Security: /cus/)
 */
export default function CustomerDashboard() {
  const router = useRouter()
  const [upcomingAppointments, setUpcomingAppointments] = useState<Appointment[]>([])
  const [recentOrders, setRecentOrders] = useState<any[]>([])
  const [recentSubscriptions, setRecentSubscriptions] = useState<any[]>([])
  const [activeCoupons, setActiveCoupons] = useState<{ code: string; name: string; discount_type: string; discount_value: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    upcomingCount: 0,
    ordersCount: 0,
    subscriptionsCount: 0,
    totalSpent: 0,
  })

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (token) {
      fetchDashboard()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      // 1. Upcoming appointments
      try {
        const params = new URLSearchParams({
          date_from: today.toISOString(),
          status: 'pending,confirmed',
        })
        const response = await apiClient.get(
          `${CUSTOMER_ENDPOINTS.APPOINTMENTS.LIST}?${params.toString()}`
        )
        const raw = response.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
        const list = raw.results ?? raw.data ?? []
        if (Array.isArray(list)) {
          const allUpcoming = list
            .filter((apt: Appointment) => new Date(apt.start_time) >= today)
            .sort((a: Appointment, b: Appointment) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
          setUpcomingAppointments(allUpcoming.slice(0, 3))
          setStats(prev => ({ ...prev, upcomingCount: allUpcoming.length }))
        }
      } catch {
        // ignore
      }

      // 2. Orders (count + recent 3)
      try {
        const orderRes = await apiClient.get(CUSTOMER_ENDPOINTS.ORDERS.LIST)
        const orderData = (orderRes.data as { data?: any[] }).data ?? (orderRes.data as { results?: any[] }).results ?? []
        const orderList = Array.isArray(orderData) ? orderData : []
        setRecentOrders(orderList.slice(0, 3))
        setStats(prev => ({ ...prev, ordersCount: orderList.length }))
      } catch {
        // ignore
      }

      // 3. Subscriptions (count + recent 3)
      try {
        const subRes = await apiClient.get(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.LIST)
        const subData = (subRes.data as { data?: any[] }).data ?? (subRes.data as { results?: any[] }).results ?? []
        const subList = Array.isArray(subData) ? subData : []
        setRecentSubscriptions(subList.slice(0, 3))
        setStats(prev => ({ ...prev, subscriptionsCount: subList.length }))
      } catch {
        // ignore
      }

      // 4. Active coupons (offers) – public endpoint
      try {
        const couponRes = await apiClient.get(PUBLIC_ENDPOINTS.COUPONS.ACTIVE)
        const couponData = (couponRes.data as { success?: boolean; data?: any[] }).data
        const list = Array.isArray(couponData) ? couponData : []
        setActiveCoupons(list.map((c: any) => ({
          code: c.code,
          name: c.name || c.code,
          discount_type: c.discount_type,
          discount_value: c.discount_value,
        })))
      } catch {
        // ignore
      }
    } catch (err: any) {
      const status = err.response?.status
      const msg = err.response?.data?.error?.message || err.response?.data?.detail
      if (status === 401) {
        setError('Please log in again.')
      } else {
        setError(msg || 'Failed to load dashboard')
      }
      console.error('Error fetching dashboard:', err)
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
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Customer Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Manage your appointments, subscriptions, and orders here.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Link href="/cus/bookings" className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="text-sm text-muted-foreground">Upcoming Appointments</div>
              <div className="text-2xl font-bold">{stats.upcomingCount}</div>
              <div className="text-xs text-primary mt-1">View all →</div>
            </Link>
            <Link href="/cus/orders" className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="text-sm text-muted-foreground">Orders</div>
              <div className="text-2xl font-bold">{stats.ordersCount}</div>
              <div className="text-xs text-primary mt-1">Manage orders →</div>
            </Link>
            <Link href="/cus/subscriptions" className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="text-sm text-muted-foreground">Subscriptions</div>
              <div className="text-2xl font-bold">{stats.subscriptionsCount}</div>
              <div className="text-xs text-primary mt-1">Manage subscriptions →</div>
            </Link>
            <Link href="/cus/payments" className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="text-sm text-muted-foreground">Payment History</div>
              <div className="text-2xl font-bold">—</div>
              <div className="text-xs text-primary mt-1">View payments →</div>
            </Link>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Current offers (active coupons) */}
          {activeCoupons.length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Current offers</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Use these codes at checkout when you book to get a discount.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {activeCoupons.map((c) => (
                  <div
                    key={c.code}
                    className="bg-card border rounded-lg p-4 flex items-center justify-between gap-3"
                  >
                    <div>
                      <div className="font-mono font-semibold text-primary">{c.code}</div>
                      <div className="text-sm text-muted-foreground">{c.name}</div>
                      <div className="text-xs mt-1">
                        {c.discount_type === 'percentage'
                          ? `${c.discount_value}% off`
                          : `£${parseFloat(c.discount_value).toFixed(2)} off`}
                      </div>
                    </div>
                    <Link
                      href="/booking"
                      className="shrink-0 text-sm font-medium text-primary hover:underline"
                    >
                      Book & use →
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            <Link href="/booking" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">📅</div>
              <div className="font-semibold">Book Service</div>
              <div className="text-sm text-muted-foreground mt-1">Schedule a new appointment</div>
            </Link>
            <Link href="/cus/bookings" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">📋</div>
              <div className="font-semibold">My Bookings</div>
              <div className="text-sm text-muted-foreground mt-1">View all appointments</div>
            </Link>
            <Link href="/cus/calendar" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">📆</div>
              <div className="font-semibold">Calendar</div>
              <div className="text-sm text-muted-foreground mt-1">View calendar & sync</div>
            </Link>
            <Link href="/cus/subscriptions" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">🔄</div>
              <div className="font-semibold">Subscriptions</div>
              <div className="text-sm text-muted-foreground mt-1">Manage recurring services</div>
            </Link>
            <Link href="/cus/orders" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">📦</div>
              <div className="font-semibold">Orders</div>
              <div className="text-sm text-muted-foreground mt-1">View multi-service orders</div>
            </Link>
            <Link href="/cus/payments" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">💳</div>
              <div className="font-semibold">Payments</div>
              <div className="text-sm text-muted-foreground mt-1">View payment history</div>
            </Link>
            <Link href="/cus/profile" className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="text-2xl mb-2">👤</div>
              <div className="font-semibold">Profile</div>
              <div className="text-sm text-muted-foreground mt-1">Manage account settings</div>
            </Link>
          </div>

          {/* Upcoming Appointments */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">Upcoming Appointments</h2>
              <Link href="/cus/bookings" className="text-primary hover:underline text-sm">
                View All →
              </Link>
            </div>
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : upcomingAppointments.length > 0 ? (
              <div className="space-y-4">
                {upcomingAppointments.map((appointment) => {
                  const { date, time } = formatDateTime(appointment.start_time)
                  return (
                    <div
                      key={appointment.id}
                      className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => router.push(`/cus/bookings/${appointment.id}`)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold">{appointment.service?.name || 'Service'}</h3>
                            <span className={`px-2 py-1 rounded text-xs ${
                              appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                              appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {appointment.status}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div>{date} at {time}</div>
                            {appointment.staff && (
                              <div>Staff: {appointment.staff.name}</div>
                            )}
                            {appointment.customer_booking && (
                              <div>Price: £{parseFloat(appointment.customer_booking.total_price.toString()).toFixed(2)}</div>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/cus/bookings/${appointment.id}`)
                          }}
                          className="text-primary hover:underline text-sm"
                        >
                          View Details →
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                No upcoming appointments
                <div className="mt-4">
                  <Link href="/booking" className="text-primary hover:underline">
                    Book a service →
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Recent Orders */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">Recent Orders</h2>
              <Link href="/cus/orders" className="text-primary hover:underline text-sm">
                View all ({stats.ordersCount}) →
              </Link>
            </div>
            {recentOrders.length > 0 ? (
              <div className="space-y-4">
                {recentOrders.map((order: any) => (
                  <Link
                    key={order.id}
                    href={`/cus/orders/${order.id}`}
                    className="block bg-card border rounded-lg p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-mono font-semibold">{order.order_number}</div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {order.scheduled_date && new Date(order.scheduled_date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}
                        </div>
                        <div className="text-sm mt-1">£{parseFloat(order.total_price || 0).toFixed(2)} · {order.status}</div>
                      </div>
                      <span className="text-primary text-sm font-medium">Manage →</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="bg-card border rounded-lg p-6 text-center text-muted-foreground">
                No orders yet. <Link href="/booking" className="text-primary hover:underline">Book an order →</Link>
              </div>
            )}
          </div>

          {/* Recent Subscriptions */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold">Recent Subscriptions</h2>
              <Link href="/cus/subscriptions" className="text-primary hover:underline text-sm">
                View all ({stats.subscriptionsCount}) →
              </Link>
            </div>
            {recentSubscriptions.length > 0 ? (
              <div className="space-y-4">
                {recentSubscriptions.map((sub: any) => (
                  <Link
                    key={sub.id}
                    href="/cus/subscriptions"
                    className="block bg-card border rounded-lg p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-mono font-semibold">{sub.subscription_number}</div>
                        <div className="text-sm text-muted-foreground mt-1">{sub.service_name || sub.service?.name}</div>
                        <div className="text-sm mt-1">£{parseFloat(sub.total_price || 0).toFixed(2)} · {sub.status}</div>
                      </div>
                      <span className="text-primary text-sm font-medium">Manage →</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="bg-card border rounded-lg p-6 text-center text-muted-foreground">
                No subscriptions yet. <Link href="/booking" className="text-primary hover:underline">Start a subscription →</Link>
              </div>
            )}
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
