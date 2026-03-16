'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { formatStatus } from '@/lib/utils'
import { DateTimeSlotPicker } from '@/components/admin/DateTimeSlotPicker'

const ORDER_STATUSES = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled'] as const
const PAYMENT_STATUSES = ['pending', 'partial', 'paid', 'refunded'] as const

interface OrderItem {
  id: number
  service: { id: number; name: string }
  staff: { id: number; name: string } | null
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
  scheduled_date: string | null
  scheduled_time: string | null
  address_line1: string
  address_line2?: string | null
  city: string
  postcode: string
  country?: string
  guest_email: string | null
  guest_name: string | null
  guest_phone?: string | null
  customer: { id: number; name: string; email: string } | null
  items: OrderItem[]
  created_at: string
}

/**
 * Admin Order Detail
 * Route: /ad/orders/[id] (Security: /ad/)
 */
export default function AdminOrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [editForm, setEditForm] = useState<{
    guest_name: string
    guest_email: string
    guest_phone: string
    scheduled_date: string
    scheduled_time: string
    address_line1: string
    address_line2: string
    city: string
    postcode: string
    country: string
  } | null>(null)

  useEffect(() => {
    fetchOrder()
  }, [id])

  const fetchOrder = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await apiClient.get(ADMIN_ENDPOINTS.ORDERS.DETAIL(id))
      if (res.data.success && res.data.data) {
        const o = res.data.data
        setOrder(o)
        setEditForm({
          guest_name: o.guest_name ?? o.customer?.name ?? '',
          guest_email: o.guest_email ?? o.customer?.email ?? '',
          guest_phone: o.guest_phone ?? '',
          scheduled_date: o.scheduled_date ? o.scheduled_date.slice(0, 10) : '',
          scheduled_time: o.scheduled_time ? String(o.scheduled_time).slice(0, 5) : '',
          address_line1: o.address_line1 ?? '',
          address_line2: o.address_line2 ?? '',
          city: o.city ?? '',
          postcode: o.postcode ?? '',
          country: o.country ?? 'United Kingdom',
        })
      } else setError('Failed to load order')
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to load order')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!order) return
    
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      
      const res = await apiClient.patch(ADMIN_ENDPOINTS.ORDERS.DETAIL(id), {
        status: newStatus
      })
      
      if (res.data.success) {
        setOrder(res.data.data)
        setMessage(`Order status updated to ${formatStatus(newStatus)}`)
        setTimeout(() => setMessage(null), 3000)
      } else {
        setError('Failed to update order status')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to update order status')
    } finally {
      setUpdating(false)
    }
  }

  const handlePaymentStatusChange = async (newPaymentStatus: string) => {
    if (!order) return
    
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      
      const res = await apiClient.patch(ADMIN_ENDPOINTS.ORDERS.DETAIL(id), {
        payment_status: newPaymentStatus
      })
      
      if (res.data.success) {
        setOrder(res.data.data)
        setMessage(`Payment status updated to ${newPaymentStatus}`)
        setTimeout(() => setMessage(null), 3000)
      } else {
        setError('Failed to update payment status')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to update payment status')
    } finally {
      setUpdating(false)
    }
  }

  const handleDelete = async () => {
    if (!order || !confirm('Delete this order? This cannot be undone.')) return
    try {
      setDeleting(true)
      setError(null)
      await apiClient.delete(ADMIN_ENDPOINTS.ORDERS.DELETE(Number(id)))
      router.push('/ad/orders')
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to delete order')
    } finally {
      setDeleting(false)
    }
  }

  const handleSaveDetails = async () => {
    if (!order || !editForm) return
    const scheduledDate = editForm.scheduled_date?.trim() || order.scheduled_date?.toString().slice(0, 10)
    if (!scheduledDate) {
      setError('Please select a date (use the calendar and pick a date, then a time slot).')
      return
    }
    if (!editForm.address_line1?.trim() || !editForm.city?.trim() || !editForm.postcode?.trim()) {
      setError('Address line 1, city and postcode are required.')
      return
    }
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      const payload: Record<string, string> = {
        guest_name: editForm.guest_name?.trim() ?? '',
        guest_email: editForm.guest_email?.trim() ?? '',
        guest_phone: editForm.guest_phone?.trim() ?? '',
        scheduled_date: scheduledDate,
        address_line1: editForm.address_line1.trim(),
        address_line2: editForm.address_line2?.trim() ?? '',
        city: editForm.city.trim(),
        postcode: editForm.postcode.trim(),
        country: editForm.country?.trim() ?? 'United Kingdom',
      }
      if (editForm.scheduled_time?.trim()) {
        const t = editForm.scheduled_time.trim()
        payload.scheduled_time = t.length === 5 ? `${t}:00` : t
      }
      const res = await apiClient.patch(ADMIN_ENDPOINTS.ORDERS.UPDATE(id), payload)
      if (res.data.success) {
        const o = res.data.data
        setOrder(o)
        setEditForm({
          guest_name: o.guest_name ?? o.customer?.name ?? '',
          guest_email: o.guest_email ?? o.customer?.email ?? '',
          guest_phone: o.guest_phone ?? '',
          scheduled_date: o.scheduled_date ? o.scheduled_date.slice(0, 10) : '',
          scheduled_time: o.scheduled_time ? String(o.scheduled_time).slice(0, 5) : '',
          address_line1: o.address_line1 ?? '',
          address_line2: o.address_line2 ?? '',
          city: o.city ?? '',
          postcode: o.postcode ?? '',
          country: o.country ?? 'United Kingdom',
        })
        setMessage('Customer, schedule and address updated.')
        setTimeout(() => setMessage(null), 3000)
      } else {
        setError(res.data?.error?.message || 'Failed to update')
      }
    } catch (e: any) {
      const err = e.response?.data
      let message = err?.error?.message
      if (!message && err?.detail) {
        if (typeof err.detail === 'string') message = err.detail
        else if (typeof err.detail === 'object' && err.detail !== null) {
          const parts = Object.entries(err.detail).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          message = parts.length ? parts.join('; ') : 'Validation error'
        }
      }
      setError(message || e.message || 'Failed to update details')
    } finally {
      setUpdating(false)
    }
  }

  const handleSendReminder = async () => {
    if (!order) return
    
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      
      const res = await apiClient.post(ADMIN_ENDPOINTS.ORDERS.SEND_REMINDER(id))
      
      if (res.data.success) {
        setMessage('Reminder email sent successfully')
        setTimeout(() => setMessage(null), 3000)
      } else {
        setError('Failed to send reminder')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to send reminder')
    } finally {
      setUpdating(false)
    }
  }

  const name = order?.customer?.name ?? order?.guest_name ?? 'Guest'

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex items-center gap-4 mb-8">
            <Button variant="outline" asChild>
              <Link href="/ad/orders">← Orders</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link href="/ad/dashboard">Dashboard</Link>
            </Button>
          </div>
          {error && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">{error}</div>
          )}
          {message && (
            <div className="mb-6 p-4 bg-green-100 text-green-800 rounded-lg">{message}</div>
          )}
          {loading ? (
            <div className="animate-pulse">Loading…</div>
          ) : order ? (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h1 className="text-2xl font-bold">{order.order_number}</h1>
                <div className="flex gap-2 items-center">
                  <span className="px-3 py-1 rounded-full bg-muted">{formatStatus(order.status)}</span>
                  <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800">
                    {formatStatus(order.payment_status)}
                  </span>
                </div>
              </div>

              {/* Order Management Actions */}
              <div className="rounded-lg border border-border p-6 bg-muted/30">
                <h2 className="font-semibold mb-4">Order Management</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Order Status</label>
                    <select
                      value={order.status}
                      onChange={(e) => handleStatusChange(e.target.value)}
                      disabled={updating}
                      className="w-full p-2 border rounded-md bg-background"
                    >
                      {ORDER_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {formatStatus(status)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Payment Status</label>
                    <select
                      value={order.payment_status}
                      onChange={(e) => handlePaymentStatusChange(e.target.value)}
                      disabled={updating}
                      className="w-full p-2 border rounded-md bg-background"
                    >
                      {PAYMENT_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {formatStatus(status)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    onClick={handleSendReminder}
                    disabled={updating}
                    variant="outline"
                  >
                    {updating ? 'Sending...' : 'Send Reminder Email'}
                  </Button>
                  <Button
                    onClick={handleDelete}
                    disabled={deleting}
                    variant="destructive"
                  >
                    {deleting ? 'Deleting...' : 'Delete Order'}
                  </Button>
                </div>
              </div>
              {/* Edit Customer, Schedule & Address */}
              {editForm && (
                <div className="rounded-lg border border-border p-6 bg-muted/20">
                  <h2 className="font-semibold mb-4">Edit Customer, Schedule & Address</h2>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Customer name</label>
                      <input
                        type="text"
                        value={editForm.guest_name}
                        onChange={(e) => setEditForm((f) => f && { ...f, guest_name: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="Name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Email</label>
                      <input
                        type="email"
                        value={editForm.guest_email}
                        onChange={(e) => setEditForm((f) => f && { ...f, guest_email: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="email@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Phone</label>
                      <input
                        type="text"
                        value={editForm.guest_phone}
                        onChange={(e) => setEditForm((f) => f && { ...f, guest_phone: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="Phone"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-2">Schedule (date & time)</label>
                      <p className="text-xs text-muted-foreground mb-2">
                        Select a date, then choose an available time slot (same as booking flow).
                      </p>
                      <DateTimeSlotPicker
                        postcode={editForm.postcode}
                        serviceId={order.items?.[0]?.service?.id ?? 0}
                        staffId={order.items?.[0]?.staff?.id}
                        selectedDate={editForm.scheduled_date}
                        selectedTime={editForm.scheduled_time}
                        onSelect={(date, time) =>
                          setEditForm((f) => f ? { ...f, scheduled_date: date, scheduled_time: time } : f)
                        }
                        disabled={updating}
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">Address line 1</label>
                      <input
                        type="text"
                        value={editForm.address_line1}
                        onChange={(e) => setEditForm((f) => f && { ...f, address_line1: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="Street address"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">Address line 2 (optional)</label>
                      <input
                        type="text"
                        value={editForm.address_line2}
                        onChange={(e) => setEditForm((f) => f && { ...f, address_line2: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="Flat, building, etc."
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">City</label>
                      <input
                        type="text"
                        value={editForm.city}
                        onChange={(e) => setEditForm((f) => f && { ...f, city: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="City"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Postcode</label>
                      <input
                        type="text"
                        value={editForm.postcode}
                        onChange={(e) => setEditForm((f) => f && { ...f, postcode: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="SW1A 2AD"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Country</label>
                      <input
                        type="text"
                        value={editForm.country}
                        onChange={(e) => setEditForm((f) => f && { ...f, country: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                        placeholder="United Kingdom"
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <Button onClick={handleSaveDetails} disabled={updating}>
                      {updating ? 'Saving...' : 'Save changes'}
                    </Button>
                  </div>
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-6 rounded-lg border border-border p-6">
                <div>
                  <h2 className="font-semibold mb-2">Customer</h2>
                  <p>{name}</p>
                  {(order.customer?.email ?? order.guest_email) && (
                    <p className="text-sm text-muted-foreground">
                      {order.customer?.email ?? order.guest_email}
                    </p>
                  )}
                </div>
                <div>
                  <h2 className="font-semibold mb-2">Schedule</h2>
                  <p>
                    {order.scheduled_date
                      ? new Date(order.scheduled_date).toLocaleDateString('en-GB', {
                          weekday: 'long',
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })
                      : '—'}
                  </p>
                  {order.scheduled_time && (
                    <p className="text-muted-foreground">{order.scheduled_time.slice(0, 5)}</p>
                  )}
                </div>
                <div className="md:col-span-2">
                  <h2 className="font-semibold mb-2">Address</h2>
                  <p>
                    {order.address_line1}
                    {order.address_line2 && `, ${order.address_line2}`}
                    <br />
                    {order.city}, {order.postcode} {order.country && `, ${order.country}`}
                  </p>
                </div>
              </div>
              <div className="rounded-lg border border-border p-6">
                <h2 className="font-semibold mb-4">Items</h2>
                <ul className="space-y-2">
                  {order.items.map((item) => (
                    <li key={item.id} className="flex justify-between py-2 border-b border-border last:border-0">
                      <span>
                        {item.service.name} × {item.quantity}
                        {item.staff && ` — ${item.staff.name}`}
                      </span>
                      <span>£{parseFloat(item.total_price).toFixed(2)}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-border font-semibold flex justify-between">
                  <span>Total</span>
                  <span>£{parseFloat(order.total_price).toFixed(2)}</span>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
