'use client'

import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { CustomerBookingsResponse } from '@/types/customer'
import { useEffect, useState } from 'react'

interface CustomerBookingsHistoryProps {
  customerId: number
}

export function CustomerBookingsHistory({ customerId }: CustomerBookingsHistoryProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<CustomerBookingsResponse['data'] | null>(null)
  const [meta, setMeta] = useState<CustomerBookingsResponse['meta'] | null>(null)

  useEffect(() => {
    fetchBookings()
  }, [customerId])

  const fetchBookings = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<CustomerBookingsResponse>(
        ADMIN_ENDPOINTS.CUSTOMERS.BOOKINGS(customerId)
      )
      
      if (response.data.success) {
        setData(response.data.data)
        setMeta(response.data.meta)
      } else {
        setError('Failed to load booking history')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load booking history')
      console.error('Error fetching bookings:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading booking history...</div>
  }

  if (error) {
    return <div className="bg-destructive/10 text-destructive p-4 rounded-lg">{error}</div>
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Appointments</div>
          <div className="text-2xl font-bold">{meta?.appointments_count || 0}</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Orders</div>
          <div className="text-2xl font-bold">{meta?.orders_count || 0}</div>
        </div>
        <div className="bg-card border rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Subscriptions</div>
          <div className="text-2xl font-bold">{meta?.subscriptions_count || 0}</div>
        </div>
      </div>

      {/* Appointments */}
      {data && data.appointments.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Appointments</h3>
          <div className="bg-card border rounded-lg overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Service</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Staff</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.appointments.map((appt: any) => (
                  <tr key={appt.id}>
                    <td className="px-4 py-3">{formatDate(appt.start_time)}</td>
                    <td className="px-4 py-3">{appt.service?.name || '-'}</td>
                    <td className="px-4 py-3">{appt.staff?.name || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        appt.status === 'completed' ? 'bg-green-100 text-green-800' :
                        appt.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {appt.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Orders */}
      {data && data.orders.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Orders</h3>
          <div className="bg-card border rounded-lg overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Order #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.orders.map((order: any) => (
                  <tr key={order.id}>
                    <td className="px-4 py-3 font-mono">{order.order_number}</td>
                    <td className="px-4 py-3">{formatDate(order.created_at)}</td>
                    <td className="px-4 py-3">£{parseFloat(order.total_price).toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        order.status === 'completed' ? 'bg-green-100 text-green-800' :
                        order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {order.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Subscriptions */}
      {data && data.subscriptions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Subscriptions</h3>
          <div className="bg-card border rounded-lg overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Subscription #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Service</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Frequency</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.subscriptions.map((sub: any) => (
                  <tr key={sub.id}>
                    <td className="px-4 py-3 font-mono">{sub.subscription_number}</td>
                    <td className="px-4 py-3">{sub.service?.name || '-'}</td>
                    <td className="px-4 py-3">{sub.frequency}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        sub.status === 'active' ? 'bg-green-100 text-green-800' :
                        sub.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {sub.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data && data.appointments.length === 0 && data.orders.length === 0 && data.subscriptions.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No booking history found
        </div>
      )}
    </div>
  )
}
