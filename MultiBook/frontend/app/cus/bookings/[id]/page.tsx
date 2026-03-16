'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, AppointmentDetailResponse } from '@/types/appointment'
import { formatDate } from '@/lib/utils'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import {
  format,
  addDays,
  addWeeks,
  subWeeks,
  isSameDay,
  isSameMonth,
  isPast,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isToday,
  startOfWeek,
  endOfWeek,
} from 'date-fns'

interface TimeSlot {
  time: string
  available: boolean
  staff_ids?: number[]
  reason?: string
}

/**
 * Customer Appointment Detail Page
 * Route: /cus/bookings/[id] (Security: /cus/)
 */
export default function CustomerAppointmentDetail() {
  const router = useRouter()
  const params = useParams()
  const appointmentId = params.id as string

  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [showReschedule, setShowReschedule] = useState(false)
  const [_newDate, setNewDate] = useState('')
  const [_newTime, setNewTime] = useState('')
  const [rescheduleSelectedDate, setRescheduleSelectedDate] = useState<Date | null>(null)
  const [rescheduleSelectedSlot, setRescheduleSelectedSlot] = useState<string | null>(null)
  const [rescheduleSlots, setRescheduleSlots] = useState<TimeSlot[]>([])
  const [rescheduleSlotsLoading, setRescheduleSlotsLoading] = useState(false)
  const [rescheduleSlotsError, setRescheduleSlotsError] = useState<string | null>(null)
  const [rescheduleCurrentMonth, setRescheduleCurrentMonth] = useState(new Date())

  useEffect(() => {
    fetchAppointment()
  }, [appointmentId])

  useEffect(() => {
    if (showReschedule && rescheduleSelectedDate) {
      fetchRescheduleSlots(rescheduleSelectedDate)
    } else if (!showReschedule) {
      setRescheduleSelectedDate(null)
      setRescheduleSelectedSlot(null)
      setRescheduleSlots([])
      setRescheduleSlotsError(null)
    } else {
      setRescheduleSlots([])
      setRescheduleSelectedSlot(null)
    }
  }, [showReschedule, rescheduleSelectedDate, appointmentId])

  const fetchAppointment = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<AppointmentDetailResponse>(
        CUSTOMER_ENDPOINTS.APPOINTMENTS.DETAIL(parseInt(appointmentId))
      )
      const raw = response.data as { success?: boolean; data?: Appointment } & Appointment
      const appointmentData = raw?.data ?? (raw?.id != null ? raw : null) as Appointment | null
      if (appointmentData?.id != null) {
        setAppointment(appointmentData)
        const currentDate = new Date(appointmentData.start_time)
        setNewDate(currentDate.toISOString().split('T')[0])
        setNewTime(currentDate.toTimeString().slice(0, 5))
      } else {
        setError('Failed to load appointment')
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message ?? err.response?.data?.detail
      setError(msg && typeof msg === 'string' ? msg : err.response?.status === 404 ? 'Appointment not found' : 'Failed to load appointment')
      console.error('Error fetching appointment:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this appointment?')) {
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      
      await apiClient.post(CUSTOMER_ENDPOINTS.APPOINTMENTS.CANCEL(parseInt(appointmentId)))
      fetchAppointment() // Refresh appointment data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to cancel appointment')
      console.error('Error cancelling appointment:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const fetchRescheduleSlots = async (date: Date) => {
    setRescheduleSlotsLoading(true)
    setRescheduleSlotsError(null)
    setRescheduleSelectedSlot(null)
    try {
      const dateStr = format(date, 'yyyy-MM-dd')
      const response = await apiClient.get(
        `${CUSTOMER_ENDPOINTS.APPOINTMENTS.AVAILABLE_SLOTS(parseInt(appointmentId))}?date=${dateStr}`
      )
      const raw = response.data as { success?: boolean; data?: { slots?: TimeSlot[] } }
      const data = raw?.data
      setRescheduleSlots(data?.slots || [])
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.error || 'Unable to load time slots'
      setRescheduleSlotsError(typeof msg === 'string' ? msg : 'Unable to load time slots')
      setRescheduleSlots([])
    } finally {
      setRescheduleSlotsLoading(false)
    }
  }

  const handleRescheduleDateSelect = (date: Date) => {
    if (isPast(date) && !isToday(date)) return
    setRescheduleSelectedDate(date)
  }

  const handleRescheduleSlotSelect = (time: string) => {
    setRescheduleSelectedSlot(time)
  }

  const formatTimeDisplay = (time: string) => {
    const [hours, minutes] = time.split(':').map(Number)
    const period = hours >= 12 ? 'PM' : 'AM'
    const hours12 = hours % 12 || 12
    return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`
  }

  const handleReschedule = async () => {
    const dateToUse = rescheduleSelectedDate
    const slotToUse = rescheduleSelectedSlot
    if (!dateToUse || !slotToUse) {
      setError('Please select a date and an available time slot')
      return
    }

    try {
      setActionLoading(true)
      setError(null)
      const [hours, minutes] = slotToUse.split(':').map(Number)
      const newDateTime = new Date(dateToUse)
      newDateTime.setHours(hours, minutes, 0, 0)
      await apiClient.post(CUSTOMER_ENDPOINTS.APPOINTMENTS.RESCHEDULE(parseInt(appointmentId)), {
        start_time: newDateTime.toISOString(),
      })
      setShowReschedule(false)
      setRescheduleSelectedDate(null)
      setRescheduleSelectedSlot(null)
      setRescheduleSlots([])
      fetchAppointment() // Refresh appointment data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to reschedule appointment')
      console.error('Error rescheduling appointment:', err)
    } finally {
      setActionLoading(false)
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
      full: date.toLocaleString('en-GB', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading appointment details...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (!appointment) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              {error || 'Appointment not found'}
            </div>
            <Button variant="outline" onClick={() => router.push('/cus/bookings')} className="mt-4">
              ← Back to Bookings
            </Button>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const { date, time, full } = formatDateTime(appointment.start_time)
  const canCancel = appointment.customer_booking?.can_cancel || false
  const canReschedule = appointment.customer_booking?.can_reschedule || false

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-8">
            <Button variant="outline" onClick={() => router.push('/cus/bookings')} className="mb-4">
              ← Back to Bookings
            </Button>
            <h1 className="text-3xl font-bold mb-2">{appointment.service?.name || 'Appointment Details'}</h1>
            <p className="text-muted-foreground">
              {full}
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
              {/* Appointment Information */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Appointment Information</h2>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Service</div>
                    <div className="font-medium">{appointment.service?.name}</div>
                    {appointment.service && (
                      <div className="text-sm text-muted-foreground mt-1">
                        Duration: {appointment.service.duration} minutes
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Date & Time</div>
                    <div className="font-medium">{date}</div>
                    <div className="text-sm text-muted-foreground">{time}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Status</div>
                    <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                      appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                      appointment.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                      appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      appointment.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {appointment.status}
                    </span>
                  </div>
                  
                  {appointment.staff && (
                    <div>
                      <div className="text-sm text-muted-foreground">Assigned Staff</div>
                      <div className="font-medium">{appointment.staff.name}</div>
                      {appointment.staff.email && (
                        <div className="text-sm text-muted-foreground">{appointment.staff.email}</div>
                      )}
                    </div>
                  )}
                  
                  {appointment.location_notes && (
                    <div>
                      <div className="text-sm text-muted-foreground">Location Notes</div>
                      <div className="text-sm whitespace-pre-wrap">{appointment.location_notes}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Payment Information */}
              {appointment.customer_booking && (
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Payment Information</h2>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Price:</span>
                      <span className="font-semibold">£{parseFloat(appointment.customer_booking.total_price.toString()).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Deposit Paid:</span>
                      <span>£{parseFloat(appointment.customer_booking.deposit_paid.toString()).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Payment Status:</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        appointment.customer_booking.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                        appointment.customer_booking.payment_status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {appointment.customer_booking.payment_status}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Reschedule: same calendar + time slots as booking/date-time */}
              {showReschedule && (
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Reschedule Appointment</h2>
                  <p className="text-sm text-muted-foreground mb-4">
                    Select a new date and time slot (same as booking). Available slots are selectable; grey slots are unavailable.
                  </p>
                  {rescheduleSlotsError && (
                    <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg text-sm">
                      {rescheduleSlotsError}
                    </div>
                  )}
                  <div className="grid md:grid-cols-2 gap-8">
                    {/* Calendar */}
                    <div>
                      <div className="border border-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-4">
                          <button
                            type="button"
                            onClick={() => setRescheduleCurrentMonth((m) => subWeeks(m, 4))}
                            className="p-2 hover:bg-muted rounded"
                          >
                            ←
                          </button>
                          <h3 className="text-lg font-semibold">
                            {format(rescheduleCurrentMonth, 'MMMM yyyy')}
                          </h3>
                          <button
                            type="button"
                            onClick={() => setRescheduleCurrentMonth((m) => addWeeks(m, 4))}
                            className="p-2 hover:bg-muted rounded"
                          >
                            →
                          </button>
                        </div>
                        <div className="grid grid-cols-7 gap-1 mb-2">
                          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                            <div key={day} className="text-center text-sm font-medium text-muted-foreground py-1">
                              {day}
                            </div>
                          ))}
                        </div>
                        <div className="grid grid-cols-7 gap-1">
                          {eachDayOfInterval({
                            start: startOfWeek(startOfMonth(rescheduleCurrentMonth), { weekStartsOn: 1 }),
                            end: endOfWeek(endOfMonth(rescheduleCurrentMonth), { weekStartsOn: 1 }),
                          }).map((day, idx) => {
                            const isCurrentMonth = isSameMonth(day, rescheduleCurrentMonth)
                            const isSelected = rescheduleSelectedDate && isSameDay(day, rescheduleSelectedDate)
                            const isTodayDate = isToday(day)
                            const isPastDate = isPast(day) && !isTodayDate
                            return (
                              <button
                                key={idx}
                                type="button"
                                onClick={() => handleRescheduleDateSelect(day)}
                                disabled={isPastDate}
                                className={`
                                  aspect-square p-1.5 rounded text-sm transition-colors
                                  ${!isCurrentMonth ? 'text-muted-foreground/50' : ''}
                                  ${isPastDate ? 'opacity-50 cursor-not-allowed' : 'hover:bg-muted cursor-pointer'}
                                  ${isSelected ? 'bg-primary text-primary-foreground' : ''}
                                  ${isTodayDate && !isSelected ? 'border-2 border-primary' : ''}
                                `}
                              >
                                {format(day, 'd')}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    </div>
                    {/* Time Slots */}
                    <div>
                      <div className="border border-border rounded-lg p-4">
                        <h3 className="text-lg font-semibold mb-3">
                          {rescheduleSelectedDate ? formatDate(rescheduleSelectedDate, 'long') : 'Select a date'}
                        </h3>
                        {rescheduleSlotsLoading ? (
                          <div className="text-center py-6 text-muted-foreground text-sm">
                            Loading available slots...
                          </div>
                        ) : !rescheduleSelectedDate ? (
                          <p className="text-sm text-muted-foreground">Select a date to see available time slots.</p>
                        ) : rescheduleSlots.length === 0 ? (
                          <div className="text-center py-6">
                            <p className="text-sm text-muted-foreground mb-2">No time slots for this date.</p>
                            <button
                              type="button"
                              onClick={() => {
                                setRescheduleCurrentMonth(addDays(rescheduleSelectedDate, 1))
                                setRescheduleSelectedDate(null)
                              }}
                              className="text-primary hover:underline text-sm"
                            >
                              Try another date
                            </button>
                          </div>
                        ) : (
                          <>
                            <p className="text-xs text-muted-foreground mb-2">
                              Available = selectable. Grey = unavailable (e.g. already booked).
                            </p>
                            <div className="grid grid-cols-3 gap-2 mb-3">
                              {rescheduleSlots.map((slot) => (
                                <button
                                  key={slot.time}
                                  type="button"
                                  onClick={() => slot.available && handleRescheduleSlotSelect(slot.time)}
                                  disabled={!slot.available}
                                  className={`
                                    p-2.5 rounded-lg border transition-colors text-sm font-medium
                                    ${!slot.available
                                      ? 'bg-muted/60 text-muted-foreground border-muted cursor-not-allowed line-through'
                                      : rescheduleSelectedSlot === slot.time
                                        ? 'bg-primary text-primary-foreground border-primary'
                                        : 'border-border hover:border-primary hover:bg-muted'
                                    }
                                  `}
                                  title={!slot.available ? (slot.reason || 'Unavailable') : undefined}
                                >
                                  {formatTimeDisplay(slot.time)}
                                  {!slot.available && slot.reason && (
                                    <span className="block text-xs mt-0.5 font-normal opacity-80">
                                      {slot.reason}
                                    </span>
                                  )}
                                </button>
                              ))}
                            </div>
                            {rescheduleSelectedSlot && (
                              <div className="flex gap-2">
                                <Button onClick={handleReschedule} disabled={actionLoading} className="flex-1">
                                  {actionLoading ? 'Processing...' : 'Confirm Reschedule'}
                                </Button>
                                <Button variant="outline" onClick={() => setShowReschedule(false)} disabled={actionLoading}>
                                  Cancel
                                </Button>
                              </div>
                            )}
                          </>
                        )}
                      </div>
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
                  {canReschedule && appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                    <Button
                      onClick={() => setShowReschedule(!showReschedule)}
                      variant="outline"
                      className="w-full"
                    >
                      {showReschedule ? 'Cancel Reschedule' : 'Reschedule'}
                    </Button>
                  )}
                  
                  {canCancel && appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                    <Button
                      onClick={handleCancel}
                      disabled={actionLoading}
                      variant="destructive"
                      className="w-full"
                    >
                      {actionLoading ? 'Processing...' : 'Cancel Appointment'}
                    </Button>
                  )}

                  {/* Order-linked appointment without customer_booking: direct to order */}
                  {!canCancel && !canReschedule && appointment.order_id && appointment.status !== 'cancelled' && appointment.status !== 'completed' && (
                    <div className="text-sm text-muted-foreground space-y-2">
                      <p>This appointment is part of your order {appointment.order_number || ''}.</p>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => router.push(`/cus/orders/${appointment.order_id}`)}
                      >
                        View order → cancel or request change
                      </Button>
                    </div>
                  )}

                  {/* Subscription-linked appointment: direct to subscription visits */}
                  {!canCancel && !canReschedule && appointment.subscription_id && appointment.status !== 'cancelled' && appointment.status !== 'completed' && !appointment.order_id && (
                    <div className="text-sm text-muted-foreground space-y-2">
                      <p>This visit is part of your subscription.</p>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => router.push(`/cus/subscriptions/${appointment.subscription_id}`)}
                      >
                        Manage visits → cancel or request change
                      </Button>
                    </div>
                  )}
                  
                  {!canCancel && !canReschedule && !appointment.order_id && !appointment.subscription_id && (
                    <div className="text-sm text-muted-foreground text-center">
                      {appointment.status === 'cancelled' && 'This appointment has been cancelled'}
                      {appointment.status === 'completed' && 'This appointment has been completed'}
                      {appointment.customer_booking && !appointment.customer_booking.can_cancel && 
                        appointment.customer_booking.cancellation_deadline && (
                        <div className="mt-2">
                          Cancellation deadline: {new Date(appointment.customer_booking.cancellation_deadline).toLocaleString()}
                        </div>
                      )}
                      {appointment.status !== 'cancelled' && appointment.status !== 'completed' && !appointment.customer_booking && (
                        <p>No actions available for this appointment.</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Info */}
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Quick Info</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Service:</span>
                    <span className="ml-2">{appointment.service?.name}</span>
                  </div>
                  {appointment.service && (
                    <div>
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="ml-2">{appointment.service.duration} minutes</span>
                    </div>
                  )}
                  {appointment.customer_booking && (
                    <div>
                      <span className="text-muted-foreground">Price:</span>
                      <span className="ml-2">£{parseFloat(appointment.customer_booking.total_price.toString()).toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
