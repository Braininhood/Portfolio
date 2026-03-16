'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface OrderItem {
  id: number
  service: {
    id: number
    name: string
  }
  quantity: number
  unit_price: string
  total_price: string
  status: string
}

interface Order {
  id: number
  order_number: string
  status: string
  total_price: string
  payment_status: string
  scheduled_date: string
  scheduled_time: string | null
  can_cancel: boolean
  can_reschedule: boolean
  items: OrderItem[]
  items_count?: number
  created_at: string
}

interface OrderListResponse {
  success: boolean
  data: Order[]
  meta?: {
    count?: number
  }
}

/**
 * Customer Orders Page
 * Route: /cus/orders (Security: /cus/)
 */
export default function CustomerOrders() {
  const router = useRouter()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    fetchOrders()
  }, [statusFilter])

  const fetchOrders = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }
      
      const response = await apiClient.get<OrderListResponse>(
        `${CUSTOMER_ENDPOINTS.ORDERS.LIST}?${params.toString()}`
      )
      
      const raw = response.data as OrderListResponse & { results?: Order[] }
      if (raw.success && (raw.data || raw.results)) {
        setOrders(Array.isArray(raw.data) ? raw.data : (raw.results ?? []))
      } else {
        setError('Failed to load orders')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load orders')
      console.error('Error fetching orders:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  const formatTime = (timeString: string | null) => {
    if (!timeString) return ''
    const [hours, minutes] = timeString.split(':')
    return `${hours}:${minutes}`
  }

  const formatCurrency = (amount: string | number) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(num)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'confirmed':
        return 'bg-blue-100 text-blue-800'
      case 'in_progress':
        return 'bg-purple-100 text-purple-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'cancelled':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">My Orders</h1>
            <p className="text-muted-foreground">
              View and manage your multi-service orders
            </p>
          </div>

          {/* Status Filter */}
          <div className="mb-6">
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                  statusFilter === 'all'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter('pending')}
                className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                  statusFilter === 'pending'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                Pending
              </button>
              <button
                onClick={() => setStatusFilter('confirmed')}
                className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                  statusFilter === 'confirmed'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                Confirmed
              </button>
              <button
                onClick={() => setStatusFilter('in_progress')}
                className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                  statusFilter === 'in_progress'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                In Progress
              </button>
              <button
                onClick={() => setStatusFilter('completed')}
                className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                  statusFilter === 'completed'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                Completed
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
              <p className="text-muted-foreground">Loading orders...</p>
            </div>
          )}

          {/* Orders List */}
          {!loading && !error && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {orders.length} order{orders.length !== 1 ? 's' : ''}
              </div>
              {orders.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  No orders found
                  <div className="mt-4">
                    <Link href="/booking" className="text-primary hover:underline">
                      Create an order →
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {orders.map((order) => (
                    <div
                      key={order.id}
                      className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => router.push(`/cus/orders/${order.id}`)}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold">Order {order.order_number}</h3>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(order.status)}`}>
                              {order.status}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              order.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                              order.payment_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {order.payment_status}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div>{formatDate(order.scheduled_date)} {order.scheduled_time && `at ${formatTime(order.scheduled_time)}`}</div>
                            <div>{order.items_count || order.items?.length || 0} service{order.items_count !== 1 ? 's' : ''}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold">{formatCurrency(order.total_price)}</div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              router.push(`/cus/orders/${order.id}`)
                            }}
                            className="text-primary hover:underline text-sm mt-2"
                          >
                            View Details →
                          </button>
                        </div>
                      </div>
                      
                      {/* Order Items Preview */}
                      {order.items && order.items.length > 0 && (
                        <div className="mt-4 pt-4 border-t">
                          <div className="text-sm font-medium mb-2">Services:</div>
                          <div className="flex flex-wrap gap-2">
                            {order.items.slice(0, 3).map((item) => (
                              <span key={item.id} className="text-sm bg-muted px-2 py-1 rounded">
                                {item.service.name} x{item.quantity}
                              </span>
                            ))}
                            {order.items.length > 3 && (
                              <span className="text-sm text-muted-foreground">
                                +{order.items.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
