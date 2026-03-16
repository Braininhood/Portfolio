'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import type { AppointmentListResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'
import Link from 'next/link'

interface PaymentEntry {
  id: string
  date: string
  service: string
  amount: number | string
  status: string
  appointmentStatus?: string
  type: 'appointment' | 'order' | 'subscription'
  link?: string
  reference?: string
}

/**
 * Customer Payment History Page
 * Route: /cus/payments (Security: /cus/)
 * Combines appointments, orders, and subscriptions into one payment history.
 */
export default function CustomerPayments() {
  const [payments, setPayments] = useState<PaymentEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    totalPaid: 0,
    totalPending: 0,
    totalRefunded: 0,
  })

  useEffect(() => {
    fetchPayments()
  }, [])

  const fetchPayments = async () => {
    try {
      setLoading(true)
      setError(null)
      const entries: PaymentEntry[] = []

      // 1. Appointments (single bookings with customer_booking)
      try {
        const aptRes = await apiClient.get<AppointmentListResponse>(CUSTOMER_ENDPOINTS.APPOINTMENTS.LIST)
        const aptData = (aptRes.data as { success?: boolean; data?: unknown[] }).data ?? (aptRes.data as { results?: unknown[] }).results ?? []
        const aptList = Array.isArray(aptData) ? aptData : []
        aptList
          .filter((apt: any) => apt.customer_booking)
          .forEach((apt: any) => {
            entries.push({
              id: `apt-${apt.id}`,
              date: apt.start_time,
              service: apt.service?.name || 'Appointment',
              amount: apt.customer_booking?.total_price ?? 0,
              status: apt.customer_booking?.payment_status || 'pending',
              appointmentStatus: apt.status,
              type: 'appointment',
              link: `/cus/bookings/${apt.id}`,
              reference: `Appointment #${apt.id}`,
            })
          })
      } catch {
        // ignore
      }

      // 2. Orders
      try {
        const orderRes = await apiClient.get(CUSTOMER_ENDPOINTS.ORDERS.LIST)
        const orderData = (orderRes.data as { data?: any[] }).data ?? (orderRes.data as { results?: any[] }).results ?? []
        const orderList = Array.isArray(orderData) ? orderData : []
        orderList.forEach((order: any) => {
          entries.push({
            id: `order-${order.id}`,
            date: order.scheduled_date || order.created_at,
            service: order.items?.length ? order.items.map((i: any) => i.service?.name).filter(Boolean).join(', ') : 'Order',
            amount: order.total_price ?? 0,
            status: order.payment_status || 'pending',
            type: 'order',
            link: `/cus/orders/${order.id}`,
            reference: order.order_number || `Order #${order.id}`,
          })
        })
      } catch {
        // ignore
      }

      // 3. Subscriptions
      try {
        const subRes = await apiClient.get(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.LIST)
        const subData = (subRes.data as { data?: any[] }).data ?? (subRes.data as { results?: any[] }).results ?? []
        const subList = Array.isArray(subData) ? subData : []
        subList.forEach((sub: any) => {
          entries.push({
            id: `sub-${sub.id}`,
            date: sub.start_date || sub.created_at,
            service: sub.service_name || sub.service?.name || 'Subscription',
            amount: sub.total_price ?? 0,
            status: sub.payment_status || 'pending',
            type: 'subscription',
            link: '/cus/subscriptions',
            reference: sub.subscription_number || `Subscription #${sub.id}`,
          })
        })
      } catch {
        // ignore
      }

      entries.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      setPayments(entries)

      const totalPaid = entries.filter(p => p.status === 'paid').reduce((sum, p) => sum + parseFloat(String(p.amount)), 0)
      const totalPending = entries.filter(p => p.status === 'pending' || p.status === 'partial').reduce((sum, p) => sum + parseFloat(String(p.amount)), 0)
      const totalRefunded = entries.filter(p => p.status === 'refunded').reduce((sum, p) => sum + parseFloat(String(p.amount)), 0)
      setStats({ totalPaid, totalPending, totalRefunded })
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load payment history')
      console.error('Error fetching payments:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(amount)
  }

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Payment History</h1>
            <p className="text-muted-foreground">
              View your payment history and invoices
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Total Paid</div>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(stats.totalPaid)}
              </div>
            </div>
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Pending Payment</div>
              <div className="text-2xl font-bold text-yellow-600">
                {formatCurrency(stats.totalPending)}
              </div>
            </div>
            <div className="bg-card border rounded-lg p-4">
              <div className="text-sm text-muted-foreground">Refunded</div>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(stats.totalRefunded)}
              </div>
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
              <p className="text-muted-foreground">Loading payment history...</p>
            </div>
          )}

          {/* Payments List */}
          {!loading && !error && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {payments.length} transaction{payments.length !== 1 ? 's' : ''}
              </div>
              {payments.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  No payment history found
                </div>
              ) : (
                <div className="bg-card border rounded-lg overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Date</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Service / Reference</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Amount</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Payment Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                        <th className="px-4 py-3 text-right text-xs font-medium uppercase">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {payments.map((payment) => (
                        <tr key={payment.id} className="hover:bg-muted/50">
                          <td className="px-4 py-3">{formatDate(payment.date)}</td>
                          <td className="px-4 py-3 capitalize">{payment.type}</td>
                          <td className="px-4 py-3">
                            <span className="font-medium">{payment.service}</span>
                            {payment.reference && (
                              <span className="block text-xs text-muted-foreground">{payment.reference}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 font-semibold">{formatCurrency(parseFloat(String(payment.amount)))}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded text-xs ${
                              payment.status === 'paid' ? 'bg-green-100 text-green-800' :
                              payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              payment.status === 'refunded' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {payment.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {payment.appointmentStatus != null ? (
                              <span className={`px-2 py-1 rounded text-xs ${
                                payment.appointmentStatus === 'completed' ? 'bg-green-100 text-green-800' :
                                payment.appointmentStatus === 'cancelled' ? 'bg-red-100 text-red-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {payment.appointmentStatus}
                              </span>
                            ) : (
                              <span className="text-muted-foreground text-xs">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {payment.link && (
                              <Link href={payment.link} className="text-primary hover:underline text-sm font-medium">
                                View
                              </Link>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
