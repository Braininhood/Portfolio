'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { formatStatus } from '@/lib/utils'
import Link from 'next/link'
import { useEffect, useState } from 'react'

interface Order {
  id: number
  order_number: string
  status: string
  total_price: string
  scheduled_date: string | null
  scheduled_time: string | null
  customer?: { name?: string } | null
  guest_name?: string | null
}

/**
 * Admin Orders List
 * Route: /ad/orders (Security: /ad/)
 */
export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const res = await apiClient.get(ADMIN_ENDPOINTS.ORDERS.LIST)
        if (res.data.success && Array.isArray(res.data.data)) setOrders(res.data.data)
        else setError('Failed to load orders')
      } catch (e) {
        setError((e as { message?: string })?.message ?? 'Failed to load orders')
      } finally {
        setLoading(false)
      }
    }
    fetchOrders()
  }, [])

  const name = (o: Order) => o.customer?.name ?? o.guest_name ?? 'Guest'

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold">Orders</h1>
            <Button asChild variant="outline">
              <Link href="/ad/dashboard">Dashboard</Link>
            </Button>
          </div>
          {error && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">{error}</div>
          )}
          {loading ? (
            <div className="animate-pulse space-y-2">Loading…</div>
          ) : (
            <div className="rounded-lg border border-border overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-3 font-medium">Order</th>
                    <th className="p-3 font-medium">Customer</th>
                    <th className="p-3 font-medium">Date</th>
                    <th className="p-3 font-medium">Total</th>
                    <th className="p-3 font-medium">Status</th>
                    <th className="p-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {orders.map((o) => (
                    <tr key={o.id} className="hover:bg-muted/50">
                      <td className="p-3 font-mono">{o.order_number}</td>
                      <td className="p-3">{name(o)}</td>
                      <td className="p-3">
                        {o.scheduled_date
                          ? new Date(o.scheduled_date).toLocaleDateString('en-GB')
                          : '—'}
                        {o.scheduled_time ? ` ${o.scheduled_time.slice(0, 5)}` : ''}
                      </td>
                      <td className="p-3">£{parseFloat(o.total_price).toFixed(2)}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded bg-muted text-sm">{formatStatus(o.status)}</span>
                      </td>
                      <td className="p-3">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/ad/orders/${o.id}`}>Manage</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {orders.length === 0 && (
                <p className="p-6 text-center text-muted-foreground">No orders</p>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
