'use client'

import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
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
  guest_name: string | null
  guest_email: string | null
  guest_phone: string | null
  created_at: string
}

interface OrderDetailResponse {
  success: boolean
  data: Order
}

/**
 * Guest Order Management Page (NO LOGIN REQUIRED)
 * Route: /guest/order/[orderNumber]
 * Perfect for elderly customers who don't want to create accounts
 */
export default function GuestOrderPage() {
  const router = useRouter()
  const params = useParams()
  const orderNumber = params.orderNumber as string

  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [showChangeRequest, setShowChangeRequest] = useState(false)
  const [newDate, setNewDate] = useState('')
  const [newTime, setNewTime] = useState('')
  const [changeReason, setChangeReason] = useState('')
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchOrder()
  }, [orderNumber])

  const fetchOrder = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<OrderDetailResponse>(
        PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER(orderNumber)
      )
      
      if (response.data.success && response.data.data) {
        setOrder(response.data.data)
        // Initialize change request form with current date/time
        const currentDate = new Date(response.data.data.scheduled_date)
        setNewDate(currentDate.toISOString().split('T')[0])
        if (response.data.data.scheduled_time) {
          setNewTime(response.data.data.scheduled_time.slice(0, 5))
        }
      } else {
        setError('Order not found')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load order')
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
      setSuccessMessage(null)
      
      await apiClient.post(PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER_CANCEL(orderNumber))
      setSuccessMessage('Order cancelled successfully')
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
      setSuccessMessage(null)
      
      await apiClient.post(PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER_REQUEST_CHANGE(orderNumber), {
        scheduled_date: newDate,
        scheduled_time: newTime || null,
        reason: changeReason,
      })
      
      setSuccessMessage('Change request submitted. A manager will review your request and contact you.')
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading order...</p>
        </div>
      </div>
    )
  }

  if (error && !order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Order Not Found</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button onClick={() => router.push('/')}>Go to Home</Button>
        </div>
      </div>
    )
  }

  if (!order) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Order Details</h1>
              <p className="text-gray-600 mt-1">Order Number: {order.order_number}</p>
            </div>
            <div className="text-right">
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                order.status === 'completed' ? 'bg-green-100 text-green-800' :
                order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                order.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                order.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {order.status.charAt(0).toUpperCase() + order.status.slice(1).replace('_', ' ')}
              </span>
            </div>
          </div>

          {/* Success/Error Messages */}
          {successMessage && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800">{successMessage}</p>
            </div>
          )}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Customer Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Customer Information</h3>
              <p className="text-gray-600">{order.guest_name || 'Guest'}</p>
              <p className="text-gray-600">{order.guest_email}</p>
              {order.guest_phone && <p className="text-gray-600">{order.guest_phone}</p>}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Service Address</h3>
              <p className="text-gray-600">{order.address_line1}</p>
              {order.address_line2 && <p className="text-gray-600">{order.address_line2}</p>}
              <p className="text-gray-600">{order.city}, {order.postcode}</p>
              <p className="text-gray-600">{order.country}</p>
            </div>
          </div>

          {/* Scheduled Date/Time */}
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">Scheduled Service</h3>
            <p className="text-gray-600">
              {formatDate(order.scheduled_date)}
              {order.scheduled_time && ` at ${formatTime(order.scheduled_time)}`}
            </p>
            {order.cancellation_deadline && (
              <p className="text-sm text-gray-500 mt-1">
                Cancellation deadline: {new Date(order.cancellation_deadline).toLocaleString('en-GB')}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {order.can_cancel && order.status !== 'cancelled' && order.status !== 'completed' && (
              <Button
                onClick={handleCancel}
                disabled={actionLoading}
                variant="destructive"
                className="min-h-[44px]"
              >
                {actionLoading ? 'Cancelling...' : 'Cancel Order'}
              </Button>
            )}
            {order.can_reschedule && order.status !== 'cancelled' && order.status !== 'completed' && (
              <Button
                onClick={() => setShowChangeRequest(!showChangeRequest)}
                disabled={actionLoading}
                variant="outline"
                className="min-h-[44px]"
              >
                {showChangeRequest ? 'Cancel Request' : 'Request Change'}
              </Button>
            )}
            {!order.can_cancel && !order.can_reschedule && (
              <p className="text-sm text-gray-500">
                This order cannot be cancelled or rescheduled (within 24 hours of scheduled time)
              </p>
            )}
          </div>

          {/* Change Request Form */}
          {showChangeRequest && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-4">Request Date/Time Change</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    New Time (Optional)
                  </label>
                  <input
                    type="time"
                    value={newTime}
                    onChange={(e) => setNewTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] text-base"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason (Optional)
                  </label>
                  <textarea
                    value={changeReason}
                    onChange={(e) => setChangeReason(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px] text-base"
                    placeholder="Please let us know why you need to reschedule..."
                  />
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={handleRequestChange}
                    disabled={actionLoading || !newDate}
                    className="min-h-[44px]"
                  >
                    {actionLoading ? 'Submitting...' : 'Submit Request'}
                  </Button>
                  <Button
                    onClick={() => {
                      setShowChangeRequest(false)
                      setChangeReason('')
                    }}
                    variant="outline"
                    disabled={actionLoading}
                    className="min-h-[44px]"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Order Items */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Services</h2>
          <div className="space-y-4">
            {order.items.map((item) => (
              <div key={item.id} className="border-b border-gray-200 pb-4 last:border-0 last:pb-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-gray-900">{item.service.name}</h3>
                    <p className="text-sm text-gray-600">
                      Quantity: {item.quantity} × {formatCurrency(item.unit_price)}
                    </p>
                    {item.staff && (
                      <p className="text-sm text-gray-600">Staff: {item.staff.name}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">{formatCurrency(item.total_price)}</p>
                    <span className={`inline-block px-2 py-1 rounded text-xs ${
                      item.status === 'completed' ? 'bg-green-100 text-green-800' :
                      item.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-gray-900">{formatCurrency(order.total_price)}</span>
            </div>
            <div className="mt-2 flex justify-between items-center text-sm text-gray-600">
              <span>Payment Status</span>
              <span className="capitalize">{order.payment_status}</span>
            </div>
            {parseFloat(order.deposit_paid) > 0 && (
              <div className="mt-2 flex justify-between items-center text-sm text-gray-600">
                <span>Deposit Paid</span>
                <span>{formatCurrency(order.deposit_paid)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Notes */}
        {order.notes && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Notes</h2>
            <p className="text-gray-600 whitespace-pre-wrap">{order.notes}</p>
          </div>
        )}
      </div>
    </div>
  )
}
