'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, AppointmentListResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

/** Order as returned from list API (minimal for display). */
interface OrderSummary {
  id: number
  order_number: string
  scheduled_date: string
  scheduled_time?: string
  status: string
}

/**
 * Customer Bookings Page
 * Route: /cus/bookings (Security: /cus/)
 * Shows single appointments and orders (multi-service). Subscriptions are on My Subscriptions.
 */
export default function CustomerBookings() {
  const router = useRouter()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past'>('upcoming')

  useEffect(() => {
    fetchBookings()
  }, [activeTab])

  const fetchBookings = async () => {
    try {
      setLoading(true)
      setError(null)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const todayStr = today.toISOString().slice(0, 10)

      const params = new URLSearchParams()
      if (activeTab === 'upcoming') {
        params.append('date_from', today.toISOString())
        params.append('status', 'pending,confirmed')
      } else {
        params.append('date_to', today.toISOString())
        params.append('status', 'completed,cancelled')
      }

      const [apptRes, orderRes] = await Promise.all([
        apiClient.get<AppointmentListResponse & { results?: Appointment[] }>(
          `${CUSTOMER_ENDPOINTS.APPOINTMENTS.LIST}?${params.toString()}`
        ),
        apiClient.get<{ success?: boolean; data?: OrderSummary[] }>(CUSTOMER_ENDPOINTS.ORDERS.LIST),
      ])

      const rawAppt = apptRes.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
      const list = rawAppt.results ?? rawAppt.data ?? []
      if (Array.isArray(list)) {
        const sorted = [...list].sort((a, b) => {
          if (activeTab === 'upcoming') {
            return new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
          }
          return new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
        })
        setAppointments(sorted)
      } else {
        setAppointments([])
      }

      const rawOrder = orderRes.data as { success?: boolean; data?: OrderSummary[] }
      const orderList = Array.isArray(rawOrder?.data) ? rawOrder.data : []
      const filtered = orderList.filter((o: OrderSummary) => {
        const sd = o.scheduled_date
        if (!sd) return false
        if (activeTab === 'upcoming') {
          return (o.status === 'confirmed' || o.status === 'pending') && sd >= todayStr
        }
        return o.status === 'completed' || o.status === 'cancelled' || sd < todayStr
      })
      const sortedOrders = [...filtered].sort((a, b) => {
        const da = a.scheduled_date + (a.scheduled_time || '00:00')
        const db = b.scheduled_date + (b.scheduled_time || '00:00')
        return activeTab === 'upcoming' ? da.localeCompare(db) : db.localeCompare(da)
      })
      setOrders(sortedOrders)
    } catch (err: any) {
      const status = err.response?.status
      const msg = err.response?.data?.error?.message || err.response?.data?.detail
      if (status === 401) {
        setError('Please log in again to view your bookings.')
      } else {
        setError(msg || 'Failed to load bookings')
      }
      console.error('Error fetching bookings:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('en-GB', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
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
            <h1 className="text-3xl font-bold mb-2">My Bookings</h1>
            <p className="text-muted-foreground">
              Appointments and orders (multi-service). For recurring subscriptions see My Subscriptions.
            </p>
            <div className="mt-3 flex flex-wrap gap-4">
              <Link href="/cus/orders" className="text-primary hover:underline font-medium">
                My Orders →
              </Link>
              <Link href="/cus/subscriptions" className="text-primary hover:underline font-medium">
                My Subscriptions →
              </Link>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b mb-6">
            <div className="flex gap-4">
              <button
                onClick={() => setActiveTab('upcoming')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'upcoming'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Upcoming
              </button>
              <button
                onClick={() => setActiveTab('past')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'past'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Past
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading bookings...</p>
            </div>
          )}

          {/* Content: Orders + Appointments */}
          {!loading && !error && (
            <>
              {/* Orders (multi-service) */}
              <h2 className="text-xl font-semibold mb-3">Orders</h2>
              {orders.length === 0 ? (
                <div className="bg-card border rounded-lg p-6 mb-8 text-center text-muted-foreground text-sm">
                  {activeTab === 'upcoming' ? 'No upcoming orders' : 'No past orders'}
                </div>
              ) : (
                <div className="space-y-3 mb-8">
                  {orders.map((order) => {
                    const orderDate = order.scheduled_date
                      ? new Date(order.scheduled_date + (order.scheduled_time ? `T${order.scheduled_time}` : 'T00:00'))
                      : null
                    const dateStr = orderDate
                      ? orderDate.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
                      : order.scheduled_date || ''
                    const timeStr = order.scheduled_time
                      ? (order.scheduled_time.includes(':') ? order.scheduled_time.slice(0, 5) : order.scheduled_time)
                      : orderDate
                        ? orderDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
                        : ''
                    return (
                      <div
                        key={order.id}
                        className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer flex justify-between items-center"
                        onClick={() => router.push(`/cus/orders/${order.id}`)}
                      >
                        <div>
                          <div className="font-medium">{order.order_number}</div>
                          <div className="text-sm text-muted-foreground">
                            {dateStr}{timeStr ? ` at ${timeStr}` : ''}
                          </div>
                          <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs ${
                            order.status === 'completed' ? 'bg-green-100 text-green-800' :
                            order.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                            order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {order.status}
                          </span>
                        </div>
                        <button
                          onClick={(e) => { e.stopPropagation(); router.push(`/cus/orders/${order.id}`) }}
                          className="text-primary hover:underline text-sm"
                        >
                          View order →
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Single appointments */}
              <h2 className="text-xl font-semibold mb-3">Single appointments</h2>
              <div className="mb-4 text-sm text-muted-foreground">
                {appointments.length} appointment{appointments.length !== 1 ? 's' : ''}
              </div>
              {appointments.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  {activeTab === 'upcoming' ? 'No upcoming appointments' : 'No past appointments'}
                  {activeTab === 'upcoming' && (
                    <div className="mt-4">
                      <button
                        onClick={() => router.push('/booking')}
                        className="text-primary hover:underline"
                      >
                        Book a service →
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {appointments.map((appointment) => {
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
                                appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                                appointment.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                                appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                appointment.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {appointment.status}
                              </span>
                            </div>
                            <div className="text-sm text-muted-foreground space-y-1">
                              <div>{date}</div>
                              <div>{time}</div>
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
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
