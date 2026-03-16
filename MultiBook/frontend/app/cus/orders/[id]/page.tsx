'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

interface OrderItem {
  id: number
  service: {
    id: number
    name: string
    duration: number
  }
  staff: {
    id: number
    name: string
  } | null
  quantity: number
  unit_price: string
  total_price: string
  status: string
  appointment: {
    id: number
    start_time: string
    end_time: string
    status: string
  } | null
}

interface Order {
  id: number
  order_number: string
  status: string
  total_price: string
  deposit_paid: string
  payment_status: string
  scheduled_date: string
  scheduled_time: string | null
  can_cancel: boolean
  can_reschedule: boolean
  cancellation_deadline: string | null
  items: OrderItem[]
  address_line1: string
  address_line2: string | null
  city: string
  postcode: string
  country: string
  notes: string | null
  created_at: string
}

interface OrderDetailResponse {
  success: boolean
  data: Order
}

/**
 * Customer Order Detail Page
 * Route: /cus/orders/[id] (Security: /cus/)
 */
export default function CustomerOrderDetail() {
  const router = useRouter()
  const params = useParams()
  const orderId = params.id as string

  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [showChangeRequest, setShowChangeRequest] = useState(false)
  const [newDate, setNewDate] = useState('')
  const [newTime, setNewTime] = useState('')
  const [changeReason, setChangeReason] = useState('')

  useEffect(() => {
    fetchOrder()
  }, [orderId])

  const fetchOrder = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get(
        CUSTOMER_ENDPOINTS.ORDERS.DETAIL(parseInt(orderId))
      )
      const raw = response.data as OrderDetailResponse & Order
      const orderData = raw?.data ?? raw
      if (orderData && (orderData.order_number != null || (orderData as Order).id != null)) {
        const o = orderData as Order
        setOrder(o)
        const currentDate = new Date(o.scheduled_date)
        setNewDate(currentDate.toISOString().split('T')[0])
        if (o.scheduled_time) {
          setNewTime(o.scheduled_time.slice(0, 5))
        }
      } else {
        setError('Order not found')
      }
    } catch (err: any) {
      const status = err.response?.status
      const message = err.response?.data?.error?.message || err.response?.data?.detail
      setError(status === 404 ? 'Order not found' : (message || 'Failed to load order'))
      console.error('Error fetching order:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this order?')) {
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      
      await apiClient.post(CUSTOMER_ENDPOINTS.ORDERS.CANCEL(parseInt(orderId)))
      fetchOrder() // Refresh order data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to cancel order')
      console.error('Error cancelling order:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleRequestChange = async () => {
    if (!newDate) {
      setError('Please select a new date')
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      
      await apiClient.post(CUSTOMER_ENDPOINTS.ORDERS.REQUEST_CHANGE(parseInt(orderId)), {
        scheduled_date: newDate,
        scheduled_time: newTime || null,
        reason: changeReason,
      })
      
      setShowChangeRequest(false)
      setChangeReason('')
      fetchOrder() // Refresh order data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to submit change request')
      console.error('Error requesting change:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
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

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading order details...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (!order) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              Order not found
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-8">
            <Button variant="outline" onClick={() => router.push('/cus/orders')} className="mb-4">
              ← Back to Orders
            </Button>
            <h1 className="text-3xl font-bold mb-2">Order {order.order_number}</h1>
            <p className="text-muted-foreground">
              {formatDate(order.scheduled_date)} {order.scheduled_time && `at ${formatTime(order.scheduled_time)}`}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Order Information */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Order Information</h2>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Order Number</div>
                    <div className="font-medium">{order.order_number}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Status</div>
                    <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                      order.status === 'completed' ? 'bg-green-100 text-green-800' :
                      order.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                      order.status === 'in_progress' ? 'bg-purple-100 text-purple-800' :
                      order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Scheduled Date & Time</div>
                    <div className="font-medium">{formatDate(order.scheduled_date)}</div>
                    {order.scheduled_time && (
                      <div className="text-sm text-muted-foreground">{formatTime(order.scheduled_time)}</div>
                    )}
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Service Address</div>
                    <div className="text-sm whitespace-pre-wrap">
                      {order.address_line1}
                      {order.address_line2 && `\n${order.address_line2}`}
                      {`\n${order.city}\n${order.postcode}`}
                      {order.country && `\n${order.country}`}
                    </div>
                  </div>
                  
                  {order.notes && (
                    <div>
                      <div className="text-sm text-muted-foreground">Notes</div>
                      <div className="text-sm whitespace-pre-wrap">{order.notes}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Order Items */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Services ({order.items.length})</h2>
                <div className="space-y-4">
                  {order.items.map((item) => (
                    <div key={item.id} className="border-b pb-4 last:border-0 last:pb-0">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium">{item.service.name}</div>
                          <div className="text-sm text-muted-foreground">
                            Quantity: {item.quantity} × {formatCurrency(item.unit_price)} = {formatCurrency(item.total_price)}
                          </div>
                          {item.staff && (
                            <div className="text-sm text-muted-foreground">
                              Staff: {item.staff.name}
                            </div>
                          )}
                          {item.appointment && (
                            <div className="text-sm text-muted-foreground mt-1">
                              Appointment: {formatDateTime(item.appointment.start_time)}
                            </div>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          item.status === 'completed' ? 'bg-green-100 text-green-800' :
                          item.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Information */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Payment Information</h2>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Price:</span>
                    <span className="font-semibold">{formatCurrency(order.total_price)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Deposit Paid:</span>
                    <span>{formatCurrency(order.deposit_paid)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Payment Status:</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      order.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                      order.payment_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {order.payment_status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Change Request Form */}
              {showChangeRequest && (
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Request Change</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">New Date</label>
                      <input
                        type="date"
                        value={newDate}
                        onChange={(e) => setNewDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">New Time (Optional)</label>
                      <input
                        type="time"
                        value={newTime}
                        onChange={(e) => setNewTime(e.target.value)}
                        className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Reason (Optional)</label>
                      <textarea
                        value={changeReason}
                        onChange={(e) => setChangeReason(e.target.value)}
                        className="w-full px-4 py-3 border rounded-md min-h-[80px]"
                        placeholder="Please explain why you need to change this order..."
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleRequestChange} disabled={actionLoading}>
                        {actionLoading ? 'Submitting...' : 'Submit Request'}
                      </Button>
                      <Button variant="outline" onClick={() => setShowChangeRequest(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions Sidebar */}
            <div className="space-y-6">
              <div className="bg-card border rounded-lg p-6 sticky top-4">
                <h2 className="text-xl font-semibold mb-4">Actions</h2>
                <div className="space-y-3">
                  {order.can_reschedule && order.status !== 'cancelled' && order.status !== 'completed' && (
                    <Button
                      onClick={() => setShowChangeRequest(!showChangeRequest)}
                      variant="outline"
                      className="w-full"
                    >
                      {showChangeRequest ? 'Cancel Request' : 'Request Change'}
                    </Button>
                  )}
                  
                  {order.can_cancel && order.status !== 'cancelled' && order.status !== 'completed' && (
                    <Button
                      onClick={handleCancel}
                      disabled={actionLoading}
                      variant="destructive"
                      className="w-full"
                    >
                      {actionLoading ? 'Processing...' : 'Cancel Order'}
                    </Button>
                  )}
                  
                  {(order.status !== 'cancelled' && order.status !== 'completed') && (order.can_cancel || order.can_reschedule) && order.cancellation_deadline && (
                    <p className="text-xs text-muted-foreground">
                      Changes and cancellations must be made at least 24 hours before. Deadline: {formatDateTime(order.cancellation_deadline)}
                    </p>
                  )}
                  {!order.can_cancel && !order.can_reschedule && order.status !== 'cancelled' && order.status !== 'completed' && (
                    <div className="text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-md">
                      The 24-hour deadline has passed. Changes and cancellations are no longer allowed. Contact us if you need help.
                      {order.cancellation_deadline && (
                        <div className="mt-1 text-xs">Deadline was: {formatDateTime(order.cancellation_deadline)}</div>
                      )}
                    </div>
                  )}
                  {(order.status === 'cancelled' || order.status === 'completed') && (
                    <div className="text-sm text-muted-foreground text-center">
                      {order.status === 'cancelled' && 'This order has been cancelled.'}
                      {order.status === 'completed' && 'This order has been completed.'}
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Info */}
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Quick Info</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Order:</span>
                    <span className="ml-2">{order.order_number}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Services:</span>
                    <span className="ml-2">{order.items.length}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Total:</span>
                    <span className="ml-2">{formatCurrency(order.total_price)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status:</span>
                    <span className="ml-2">{order.status}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
