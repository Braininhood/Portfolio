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

const APPOINTMENT_STATUSES = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'] as const

interface Appointment {
  id: number
  order_number?: string | null
  subscription_number?: string | null
  staff: {
    id: number
    name: string
  }
  service: {
    id: number
    name: string
    duration?: number
  }
  order_id?: number | null
  start_time: string
  end_time: string
  status: string
  appointment_type: string
  customer_booking?: {
    customer: {
      id: number
      name: string
      email: string
    }
    total_price: string
    payment_status: string
  } | null
  internal_notes?: string | null
  location_notes?: string | null
}

/**
 * Admin Appointment Detail
 * Route: /ad/appointments/[id] (Security: /ad/)
 */
export default function AdminAppointmentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [slotDate, setSlotDate] = useState('')
  const [slotTime, setSlotTime] = useState('')
  const [order, setOrder] = useState<{
    id: number
    postcode: string
    guest_name: string | null
    guest_email: string | null
    guest_phone?: string | null
    address_line1: string
    address_line2?: string | null
    city: string
    country?: string
  } | null>(null)
  const [orderEditForm, setOrderEditForm] = useState<{
    guest_name: string
    guest_email: string
    guest_phone: string
    address_line1: string
    address_line2: string
    city: string
    postcode: string
    country: string
  } | null>(null)

  useEffect(() => {
    fetchAppointment()
  }, [id])

  useEffect(() => {
    if (appointment?.start_time) {
      const d = new Date(appointment.start_time)
      setSlotDate(d.toISOString().slice(0, 10))
      setSlotTime(d.toTimeString().slice(0, 5))
    }
  }, [appointment?.start_time])

  useEffect(() => {
    if (!appointment?.order_id) return
    apiClient
      .get(ADMIN_ENDPOINTS.ORDERS.DETAIL(appointment.order_id))
      .then((res) => {
        if (res.data?.success && res.data?.data) {
          const o = res.data.data
          setOrder(o)
          setOrderEditForm({
            guest_name: o.guest_name ?? o.customer?.name ?? '',
            guest_email: o.guest_email ?? o.customer?.email ?? '',
            guest_phone: o.guest_phone ?? '',
            address_line1: o.address_line1 ?? '',
            address_line2: o.address_line2 ?? '',
            city: o.city ?? '',
            postcode: o.postcode ?? '',
            country: o.country ?? 'United Kingdom',
          })
        }
      })
      .catch(() => setOrder(null))
  }, [appointment?.order_id])

  const fetchAppointment = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await apiClient.get(ADMIN_ENDPOINTS.APPOINTMENTS.DETAIL(id))
      if (res.data.success && res.data.data) {
        setAppointment(res.data.data)
      } else {
        setError('Failed to load appointment')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to load appointment')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!appointment || !confirm('Delete this appointment? This cannot be undone.')) return
    try {
      setDeleting(true)
      setError(null)
      await apiClient.delete(ADMIN_ENDPOINTS.APPOINTMENTS.DELETE(Number(id)))
      router.push('/ad/appointments')
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to delete appointment')
    } finally {
      setDeleting(false)
    }
  }

  const handleSaveDateTime = async () => {
    if (!appointment || !slotDate || !slotTime) return
    const durationMin = appointment.service?.duration ?? 60
    const startDt = new Date(`${slotDate}T${slotTime}:00`)
    const endDt = new Date(startDt.getTime() + durationMin * 60 * 1000)
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      const res = await apiClient.patch(ADMIN_ENDPOINTS.APPOINTMENTS.UPDATE(id), {
        start_time: startDt.toISOString(),
        end_time: endDt.toISOString(),
      })
      if (res.data.success) {
        setAppointment(res.data.data)
        setMessage('Date and time updated.')
        setTimeout(() => setMessage(null), 3000)
      } else setError('Failed to update date/time')
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to update date and time')
    } finally {
      setUpdating(false)
    }
  }

  const handleSaveOrderDetails = async () => {
    if (!order || !orderEditForm || !appointment?.order_id) return
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      const res = await apiClient.patch(ADMIN_ENDPOINTS.ORDERS.UPDATE(appointment.order_id), {
        guest_name: orderEditForm.guest_name || null,
        guest_email: orderEditForm.guest_email || null,
        guest_phone: orderEditForm.guest_phone || null,
        address_line1: orderEditForm.address_line1,
        address_line2: orderEditForm.address_line2 || null,
        city: orderEditForm.city,
        postcode: orderEditForm.postcode,
        country: orderEditForm.country,
      })
      if (res.data?.success && res.data?.data) {
        setOrder(res.data.data)
        setMessage('Customer and address updated.')
        setTimeout(() => setMessage(null), 3000)
      } else setError('Failed to update')
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to update customer/address')
    } finally {
      setUpdating(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!appointment) return
    
    try {
      setUpdating(true)
      setError(null)
      setMessage(null)
      
      const res = await apiClient.patch(ADMIN_ENDPOINTS.APPOINTMENTS.UPDATE(id), {
        status: newStatus
      })
      
      if (res.data.success) {
        setAppointment(res.data.data)
        setMessage(`Appointment status updated to ${formatStatus(newStatus)}`)
        setTimeout(() => setMessage(null), 3000)
      } else {
        setError('Failed to update appointment status')
      }
    } catch (e: any) {
      setError(e.response?.data?.error?.message || 'Failed to update appointment status')
    } finally {
      setUpdating(false)
    }
  }

  const getCustomerName = () => {
    if (appointment?.customer_booking?.customer) {
      return appointment.customer_booking.customer.name
    }
    return 'Guest'
  }

  const getCustomerEmail = () => {
    if (appointment?.customer_booking?.customer) {
      return appointment.customer_booking.customer.email
    }
    return null
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex items-center gap-4 mb-8">
            <Button variant="outline" asChild>
              <Link href="/ad/appointments">← Appointments</Link>
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
          ) : appointment ? (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h1 className="text-2xl font-bold">Appointment #{appointment.id}</h1>
                <span className={`px-3 py-1 rounded-full ${
                  appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                  appointment.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                  appointment.status === 'in_progress' ? 'bg-purple-100 text-purple-800' :
                  appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {formatStatus(appointment.status)}
                </span>
              </div>

              {/* Appointment Management */}
              <div className="rounded-lg border border-border p-6 bg-muted/30">
                <h2 className="font-semibold mb-4">Appointment Management</h2>
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-sm font-medium mb-2">Status</label>
                    <select
                      value={appointment.status}
                      onChange={(e) => handleStatusChange(e.target.value)}
                      disabled={updating}
                      className="w-full p-2 border rounded-md bg-background"
                    >
                      {APPOINTMENT_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {formatStatus(status)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    onClick={handleDelete}
                    disabled={deleting}
                    variant="destructive"
                  >
                    {deleting ? 'Deleting...' : 'Delete Appointment'}
                  </Button>
                </div>
              </div>

              {/* Edit date & time (same UX as booking) */}
              <div className="rounded-lg border border-border p-6 bg-muted/20">
                <h2 className="font-semibold mb-4">Edit Date & Time</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Select a date and time slot (same as booking flow). Staff availability is checked when you save.
                </p>
                {order?.postcode ? (
                  <>
                    <DateTimeSlotPicker
                      postcode={order.postcode}
                      serviceId={appointment.service.id}
                      staffId={appointment.staff.id}
                      selectedDate={slotDate}
                      selectedTime={slotTime}
                      onSelect={(date, time) => {
                        setSlotDate(date)
                        setSlotTime(time)
                      }}
                      disabled={updating}
                    />
                    <div className="mt-4">
                      <Button
                        onClick={handleSaveDateTime}
                        disabled={updating || !slotDate || !slotTime}
                      >
                        {updating ? 'Saving...' : 'Save date & time'}
                      </Button>
                    </div>
                  </>
                ) : (
                  <p className="text-muted-foreground text-sm">
                    Load order to pick date/time (postcode needed for slots). This appointment may not be linked to an order.
                  </p>
                )}
              </div>

              {/* Edit Customer & Address (from order) */}
              {order && orderEditForm && (
                <div className="rounded-lg border border-border p-6 bg-muted/20">
                  <h2 className="font-semibold mb-4">Edit Customer & Address</h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    This appointment is linked to an order. Edit customer and address here (saves to the order).
                  </p>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Customer name</label>
                      <input
                        type="text"
                        value={orderEditForm.guest_name}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, guest_name: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Email</label>
                      <input
                        type="email"
                        value={orderEditForm.guest_email}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, guest_email: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Phone</label>
                      <input
                        type="text"
                        value={orderEditForm.guest_phone}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, guest_phone: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">Address line 1</label>
                      <input
                        type="text"
                        value={orderEditForm.address_line1}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, address_line1: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">Address line 2 (optional)</label>
                      <input
                        type="text"
                        value={orderEditForm.address_line2}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, address_line2: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">City</label>
                      <input
                        type="text"
                        value={orderEditForm.city}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, city: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Postcode</label>
                      <input
                        type="text"
                        value={orderEditForm.postcode}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, postcode: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Country</label>
                      <input
                        type="text"
                        value={orderEditForm.country}
                        onChange={(e) => setOrderEditForm((f) => f && { ...f, country: e.target.value })}
                        className="w-full p-2 border rounded-md bg-background"
                      />
                    </div>
                  </div>
                  <div className="mt-4">
                    <Button onClick={handleSaveOrderDetails} disabled={updating}>
                      {updating ? 'Saving...' : 'Save customer & address'}
                    </Button>
                  </div>
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-6 rounded-lg border border-border p-6">
                <div>
                  <h2 className="font-semibold mb-2">Service</h2>
                  <p>{appointment.service.name}</p>
                </div>
                <div>
                  <h2 className="font-semibold mb-2">Staff</h2>
                  <p>{appointment.staff.name}</p>
                </div>
                <div>
                  <h2 className="font-semibold mb-2">Customer</h2>
                  <p>{getCustomerName()}</p>
                  {getCustomerEmail() && (
                    <p className="text-sm text-muted-foreground">{getCustomerEmail()}</p>
                  )}
                </div>
                <div>
                  <h2 className="font-semibold mb-2">Type</h2>
                  <p className="capitalize">{appointment.appointment_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <h2 className="font-semibold mb-2">Start Time</h2>
                  <p>
                    {new Date(appointment.start_time).toLocaleString('en-GB', {
                      weekday: 'long',
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                <div>
                  <h2 className="font-semibold mb-2">End Time</h2>
                  <p>
                    {new Date(appointment.end_time).toLocaleString('en-GB', {
                      weekday: 'long',
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                {appointment.order_number && (
                  <div>
                    <h2 className="font-semibold mb-2">Order Number</h2>
                    <Link href={`/ad/orders/${appointment.order_number}`} className="text-primary hover:underline">
                      {appointment.order_number}
                    </Link>
                  </div>
                )}
                {appointment.subscription_number && (
                  <div>
                    <h2 className="font-semibold mb-2">Subscription Number</h2>
                    <p>{appointment.subscription_number}</p>
                  </div>
                )}
              </div>

              {appointment.customer_booking && (
                <div className="rounded-lg border border-border p-6">
                  <h2 className="font-semibold mb-4">Booking Details</h2>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Price</p>
                      <p className="font-semibold">£{parseFloat(appointment.customer_booking.total_price).toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Payment Status</p>
                      <p className="capitalize">{appointment.customer_booking.payment_status}</p>
                    </div>
                  </div>
                </div>
              )}

              {(appointment.internal_notes || appointment.location_notes) && (
                <div className="rounded-lg border border-border p-6">
                  <h2 className="font-semibold mb-4">Notes</h2>
                  {appointment.internal_notes && (
                    <div className="mb-4">
                      <p className="text-sm text-muted-foreground mb-1">Internal Notes</p>
                      <p className="whitespace-pre-wrap">{appointment.internal_notes}</p>
                    </div>
                  )}
                  {appointment.location_notes && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">Location Notes</p>
                      <p className="whitespace-pre-wrap">{appointment.location_notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
