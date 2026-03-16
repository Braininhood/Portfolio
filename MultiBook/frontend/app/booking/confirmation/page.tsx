'use client'

/**
 * Booking Step 7: Confirmation & Account Linking
 * Route: /booking/confirmation (Public - Guest Checkout)
 * 
 * After order completion:
 * - Show confirmation with order number and tracking token
 * - Option to login and link order to account (if email matches)
 * - Option to register (pre-filled details)
 * - Option to skip (guest order continues to work)
 */
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { AccountLinkingModal } from '@/components/booking/AccountLinkingModal'
import { Button } from '@/components/ui/button'
import { useBookingStore } from '@/store/booking-store'

interface OrderData {
  id: number
  order_number: string
  tracking_token: string
  status: string
  total_price: string
  scheduled_date: string
  scheduled_time: string
  guest_email?: string
  guest_name?: string
  is_guest_order: boolean
  address_line1?: string
  address_line2?: string
  city?: string
  postcode?: string
  country?: string
  items?: Array<{ service?: { name?: string }; quantity?: number }>
  customer?: {
    id: number
    name?: string
    email?: string
    phone?: string
    user_id?: number | null
    has_user_account?: boolean
  } | null
}

interface SubscriptionData {
  id: number
  subscription_number: string
  tracking_token: string
  status: string
  frequency: string
  duration_months: number
  start_date: string
  end_date: string
  total_appointments: number
  total_price: string
  payment_status?: string
  service?: { name?: string; duration?: number }
  guest_email?: string
  guest_name?: string
  is_guest_subscription?: boolean
  customer?: { id: number; email?: string; user_id?: number | null; has_user_account?: boolean } | null
  address_line1?: string
  address_line2?: string
  city?: string
  postcode?: string
  country?: string
  appointments?: Array<{
    scheduled_date: string
    appointment?: { start_time?: string }
  }>
}

/** Build location string for calendar event from order address. */
function orderLocation(order: OrderData): string {
  const parts = [
    order.address_line1,
    order.address_line2,
    order.city,
    order.postcode,
    order.country,
  ].filter(Boolean)
  return parts.join(', ')
}

/** Build event title from order (service names or fallback). */
function orderEventTitle(order: OrderData): string {
  if (order.items?.length) {
    const names = order.items
      .map((i) => (i.quantity && i.quantity > 1 ? `${i.service?.name || 'Service'} × ${i.quantity}` : i.service?.name || 'Service'))
      .filter(Boolean)
    if (names.length) return `MultiBook – ${names.join(', ')}`
  }
  return `MultiBook Booking – ${order.order_number}`
}

/** Format YYYYMMDD and HHmm for .ics / Google Calendar. */
function formatCalendarDateTime(dateStr: string, timeStr: string, durationMinutes = 60): { start: string; end: string; startGoogle: string; endGoogle: string } {
  const date = new Date(dateStr)
  const [h = 0, m = 0] = timeStr.split(':').map(Number)
  date.setHours(h, m, 0, 0)
  const y = date.getFullYear()
  const mo = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const endDate = new Date(date.getTime() + durationMinutes * 60 * 1000)
  const ey = endDate.getFullYear()
  const emo = String(endDate.getMonth() + 1).padStart(2, '0')
  const ed = String(endDate.getDate()).padStart(2, '0')
  const ehh = String(endDate.getHours()).padStart(2, '0')
  const emm = String(endDate.getMinutes()).padStart(2, '0')
  return {
    start: `${y}${mo}${d}T${hh}${mm}00`,
    end: `${ey}${emo}${ed}T${ehh}${emm}00`,
    startGoogle: `${y}${mo}${d}T${hh}${mm}00`,
    endGoogle: `${ey}${emo}${ed}T${ehh}${emm}00`,
  }
}

/** Generate .ics file content for the order and trigger download. */
function downloadIcs(order: OrderData): void {
  const title = orderEventTitle(order)
  const location = orderLocation(order)
  const { start, end } = formatCalendarDateTime(order.scheduled_date, order.scheduled_time || '09:00:00')
  const description = `Order ${order.order_number}. Total: £${parseFloat(order.total_price).toFixed(2)}.`
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//MultiBook//Booking//EN',
    'BEGIN:VEVENT',
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${title.replace(/\n/g, ' ')}`,
    `DESCRIPTION:${description.replace(/\n/g, ' ')}`,
    location ? `LOCATION:${location.replace(/\n/g, ' ')}` : '',
    `UID:multibook-${order.order_number}@multibook`,
    'END:VEVENT',
    'END:VCALENDAR',
  ]
    .filter(Boolean)
    .join('\r\n')
  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `multibook-booking-${order.order_number}.ics`
  a.click()
  URL.revokeObjectURL(url)
}

/** Open Google Calendar with pre-filled event in new tab. */
function openGoogleCalendar(order: OrderData): void {
  const title = encodeURIComponent(orderEventTitle(order))
  const location = encodeURIComponent(orderLocation(order))
  const { startGoogle, endGoogle } = formatCalendarDateTime(order.scheduled_date, order.scheduled_time || '09:00:00')
  const description = encodeURIComponent(
    `Order ${order.order_number}. Total: £${parseFloat(order.total_price).toFixed(2)}.`
  )
  const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startGoogle}/${endGoogle}&details=${description}${location ? `&location=${location}` : ''}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

/** Build subscription event title for calendar. */
function subscriptionEventTitle(sub: SubscriptionData): string {
  const name = sub.service?.name || 'Subscription'
  return `MultiBook – ${name} (Subscription)`
}

/** Build location string for subscription (address if present). */
function subscriptionLocation(sub: SubscriptionData): string {
  const parts = [sub.address_line1, sub.address_line2, sub.city, sub.postcode, sub.country].filter(Boolean)
  return parts.join(', ')
}

/** Get first appointment date and time from subscription, or start_date at 09:00. */
function subscriptionFirstDateTime(sub: SubscriptionData): { dateStr: string; timeStr: string } {
  const first = sub.appointments?.[0]
  if (first?.scheduled_date) {
    const t = first.appointment?.start_time
    let timeStr = '09:00:00'
    if (t && typeof t === 'string') {
      if (t.includes('T')) {
        const d = new Date(t)
        timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
      } else {
        timeStr = t.slice(0, 8) || timeStr
      }
    }
    return { dateStr: first.scheduled_date, timeStr }
  }
  return { dateStr: sub.start_date, timeStr: '09:00:00' }
}

/** Download .ics for subscription (first visit). */
function downloadSubscriptionIcs(sub: SubscriptionData): void {
  const title = subscriptionEventTitle(sub)
  const location = subscriptionLocation(sub)
  const { dateStr, timeStr } = subscriptionFirstDateTime(sub)
  const durationMinutes = sub.service?.duration ?? 60
  const { start, end } = formatCalendarDateTime(dateStr, timeStr, durationMinutes)
  const description = `Subscription ${sub.subscription_number}. ${sub.service?.name || 'Service'}. Total: £${parseFloat(sub.total_price).toFixed(2)}.`
  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//MultiBook//Subscription//EN',
    'BEGIN:VEVENT',
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${title.replace(/\n/g, ' ')}`,
    `DESCRIPTION:${description.replace(/\n/g, ' ')}`,
    location ? `LOCATION:${location.replace(/\n/g, ' ')}` : '',
    `UID:multibook-sub-${sub.subscription_number}@multibook`,
    'END:VEVENT',
    'END:VCALENDAR',
  ]
    .filter(Boolean)
    .join('\r\n')
  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `multibook-subscription-${sub.subscription_number}.ics`
  a.click()
  URL.revokeObjectURL(url)
}

/** Open Google Calendar for subscription first visit. */
function openSubscriptionGoogleCalendar(sub: SubscriptionData): void {
  const title = encodeURIComponent(subscriptionEventTitle(sub))
  const location = encodeURIComponent(subscriptionLocation(sub))
  const { dateStr, timeStr } = subscriptionFirstDateTime(sub)
  const durationMinutes = sub.service?.duration ?? 60
  const { startGoogle, endGoogle } = formatCalendarDateTime(dateStr, timeStr, durationMinutes)
  const description = encodeURIComponent(
    `Subscription ${sub.subscription_number}. Total: £${parseFloat(sub.total_price).toFixed(2)}.`
  )
  const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${startGoogle}/${endGoogle}&details=${description}${location ? `&location=${location}` : ''}`
  window.open(url, '_blank', 'noopener,noreferrer')
}

function ConfirmationPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const resetBooking = useBookingStore((s) => s.resetBooking)

  const [order, setOrder] = useState<OrderData | null>(null)
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [emailExists, setEmailExists] = useState<boolean | null>(null)
  const [showLinkingModal, setShowLinkingModal] = useState(false)
  const [isLinked, setIsLinked] = useState(false)
  const [orderNumber, setOrderNumber] = useState<string | null>(null)
  const [subscriptionNumber, setSubscriptionNumber] = useState<string | null>(null)

  useEffect(() => {
    const getParams = () => {
      if (typeof window === 'undefined') return { order: null as string | null, subscription: null as string | null }
      const urlParams = new URLSearchParams(window.location.search)
      let orderNum = urlParams.get('order')
      let subNum = urlParams.get('subscription')
      if (!orderNum && !subNum) {
        try {
          orderNum = searchParams.get('order')
          subNum = searchParams.get('subscription')
        } catch {
          // ignore
        }
      }
      return { order: orderNum, subscription: subNum }
    }

    const { order: orderNum, subscription: subNum } = getParams()
    if (orderNum) {
      setOrderNumber(orderNum)
      setSubscriptionNumber(null)
      return
    }
    if (subNum) {
      setSubscriptionNumber(subNum)
      setOrderNumber(null)
      return
    }

    const timers: NodeJS.Timeout[] = []
    const quickRetry = setTimeout(() => {
      const p = getParams()
      if (p.order) {
        setOrderNumber(p.order)
        setSubscriptionNumber(null)
        timers.forEach(t => clearTimeout(t))
      } else if (p.subscription) {
        setSubscriptionNumber(p.subscription)
        setOrderNumber(null)
        timers.forEach(t => clearTimeout(t))
      }
    }, 100)
    timers.push(quickRetry)

    const finalCheck = setTimeout(() => {
      const p = getParams()
      if (p.order) {
        setOrderNumber(p.order)
        setSubscriptionNumber(null)
      } else if (p.subscription) {
        setSubscriptionNumber(p.subscription)
        setOrderNumber(null)
      } else {
        router.replace('/booking/postcode')
      }
    }, 3000)
    timers.push(finalCheck)

    return () => { timers.forEach(t => clearTimeout(t)) }
  }, [searchParams, router])

  useEffect(() => {
    if (!subscriptionNumber) return
    let cancelled = false
    setLoading(true)
    setError(null)
    const fetchSub = async () => {
      try {
        const response = await apiClient.get(PUBLIC_ENDPOINTS.BOOKINGS.GUEST_SUBSCRIPTION(subscriptionNumber))
        if (cancelled) return
        if (response.data.success && response.data.data) {
          setSubscription(response.data.data)
          const subData = response.data.data as SubscriptionData
          const hasUser = subData.customer?.user_id ?? subData.customer?.has_user_account
          setIsLinked(!!hasUser)
        } else {
          setError('Subscription not found')
        }
      } catch (err: unknown) {
        if (cancelled) return
        const status = (err as { response?: { status?: number } })?.response?.status
        setError(status === 404 ? 'Subscription not found' : 'Unable to load subscription details')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchSub()
    return () => { cancelled = true }
  }, [subscriptionNumber])

  useEffect(() => {
    if (!orderNumber) {
      if (!subscriptionNumber) setLoading(true)
      return
    }

    let cancelled = false
    const fetchOrder = async () => {
      setLoading(true)
      setError(null)
      const endpoint = PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER(orderNumber)

      try {
        const response = await apiClient.get(endpoint)
        if (cancelled) return

        if (response.data.success && response.data.data) {
          const orderData = response.data.data
          setOrder(orderData)
          const hasUserAccount = orderData.customer?.has_user_account || orderData.customer?.user_id
          setIsLinked(!!hasUserAccount)
          const orderEmail = orderData.guest_email || orderData.customer?.email
          if (orderEmail && !hasUserAccount) {
            try {
              const emailCheckResponse = await apiClient.post(
                PUBLIC_ENDPOINTS.BOOKINGS.GUEST_CHECK_EMAIL,
                { email: orderEmail }
              )
              if (!cancelled && emailCheckResponse.data.success) {
                setEmailExists(emailCheckResponse.data.data?.email_exists ?? false)
              }
            } catch {
              // Optional: ignore
            }
          }
        } else {
          setError('Order not found')
        }
      } catch (err: unknown) {
        if (cancelled) return
        const status = (err as { response?: { status?: number; data?: { error?: { message?: string } } } })?.response?.status
        const message = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message
        setError(status === 404 ? 'Order not found' : (message || 'Unable to load order details'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchOrder()
    return () => { cancelled = true }
  }, [orderNumber, subscriptionNumber])

  if (loading) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-center min-h-[400px]">
            <p className="text-muted-foreground">Loading confirmation...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!loading && error && (orderNumber || subscriptionNumber)) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <div className="p-6 bg-destructive/10 text-destructive rounded-lg">
            {error}
          </div>
          <div className="mt-4">
            <Link
              href="/booking"
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors inline-block"
            >
              Start New Booking
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const hasRef = orderNumber || subscriptionNumber
  const hasData = order || subscription
  if (loading || (hasRef && !hasData)) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground mb-2">Loading confirmation...</p>
              {orderNumber && <p className="text-xs text-muted-foreground">Order: {orderNumber}</p>}
              {subscriptionNumber && <p className="text-xs text-muted-foreground">Subscription: {subscriptionNumber}</p>}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Subscription confirmation
  if (subscription) {
    const subTrackPath = `/booking/track/${subscription.tracking_token}`
    const freqLabel = subscription.frequency === 'weekly' ? 'Every week' : subscription.frequency === 'biweekly' ? 'Every 2 weeks' : 'Every month'
    const firstVisits = (subscription.appointments || [])
      .filter((a) => a.scheduled_date && a.appointment?.start_time)
      .slice(0, 10)
      .map((a) => {
        const t = a.appointment!.start_time
        const timeStr = typeof t === 'string' && t.includes('T')
          ? new Date(t).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
          : typeof t === 'string'
            ? t.slice(0, 5)
            : ''
        return { date: a.scheduled_date, time: timeStr }
      })
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <div className="mb-4">
              <div className="inline-block p-4 bg-green-100 dark:bg-green-900 rounded-full mb-4">
                <svg className="w-12 h-12 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <h1 className="text-3xl font-bold mb-2">Subscription confirmed!</h1>
            <p className="text-muted-foreground">
              Thank you. Your recurring booking is set up. We&apos;ll send a confirmation to {subscription.guest_email || subscription.customer?.email}.
            </p>
          </div>
          <div className="mb-8 p-6 border border-border rounded-lg space-y-4">
            <h2 className="text-xl font-semibold">Subscription details</h2>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Subscription number:</span>
                <span className="font-mono font-semibold">{subscription.subscription_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status:</span>
                <span className="font-medium capitalize">{subscription.status}</span>
              </div>
              {subscription.service?.name && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Service:</span>
                  <span className="font-medium">{subscription.service.name}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Frequency:</span>
                <span className="font-medium">{freqLabel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Duration:</span>
                <span className="font-medium">{subscription.duration_months} month{subscription.duration_months !== 1 ? 's' : ''}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Start date:</span>
                <span className="font-medium">
                  {new Date(subscription.start_date).toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total:</span>
                <span className="font-medium">£{parseFloat(subscription.total_price).toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Your scheduled visits (if we have appointment times) */}
          {firstVisits.length > 0 && (
            <div className="mb-8 p-6 border border-border rounded-lg">
              <h3 className="font-semibold mb-2">Your scheduled visits</h3>
              <p className="text-sm text-muted-foreground mb-3">
                If your preferred day or time wasn’t available, we’ve used the next available slot. You can manage or reschedule from My Subscriptions.
              </p>
              <ul className="text-sm space-y-1">
                {firstVisits.map((v, i) => (
                  <li key={i}>
                    {new Date(v.date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}
                    {v.time ? ` at ${v.time}` : ''}
                  </li>
                ))}
              </ul>
              {subscription.total_appointments > firstVisits.length && (
                <p className="text-xs text-muted-foreground mt-2">
                  + {subscription.total_appointments - firstVisits.length} more visit{subscription.total_appointments - firstVisits.length !== 1 ? 's' : ''} (see confirmation email for full list)
                </p>
              )}
            </div>
          )}

          {/* Add to calendar */}
          <div className="mb-8 p-6 border border-border rounded-lg">
            <h3 className="font-semibold mb-2">Add to calendar</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Add your first visit to your calendar. Exact times for later visits will be in your confirmation email.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => downloadSubscriptionIcs(subscription)}>
                Download .ics file
              </Button>
              <Button variant="outline" onClick={() => openSubscriptionGoogleCalendar(subscription)}>
                Add to Google Calendar
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <Link href={subTrackPath} className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors inline-block">
              View subscription
            </Link>
            <Link href="/cus/subscriptions" className="px-6 py-3 border border-border rounded-lg hover:bg-muted inline-block">
              My Subscriptions
            </Link>
            <Link href="/booking" className="px-6 py-3 border border-border rounded-lg hover:bg-muted inline-block">
              Create new order
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Order confirmation (existing UI)
  const trackPagePath = `/booking/track/${order!.tracking_token}`

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="mb-4">
            <div className="inline-block p-4 bg-green-100 dark:bg-green-900 rounded-full mb-4">
              <svg
                className="w-12 h-12 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </div>
          <h1 className="text-3xl font-bold mb-2">Booking Confirmed!</h1>
          <p className="text-muted-foreground">
            Thank you for your booking. We&apos;ve sent a confirmation email to {order!.guest_email || order!.customer?.email}.
          </p>
        </div>

        {/* Order Details */}
        <div className="mb-8 p-6 border border-border rounded-lg space-y-4">
          <h2 className="text-xl font-semibold">Order Details</h2>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Order Number:</span>
              <span className="font-mono font-semibold">{order!.order_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status:</span>
              <span className="font-medium capitalize">{order!.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total:</span>
              <span className="font-medium">£{parseFloat(order!.total_price).toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Scheduled Date:</span>
              <span className="font-medium">
                {new Date(order!.scheduled_date).toLocaleDateString('en-GB', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
            {order!.scheduled_time && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time:</span>
                <span className="font-medium">
                  {new Date(`2000-01-01T${order!.scheduled_time}`).toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Track order status (button only – no token/URL shown) */}
        <div className="mb-8 p-6 bg-muted rounded-lg">
          <h3 className="font-semibold mb-2">Track your order</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Check your order status anytime. A link has been sent to your email.
          </p>
          <Button asChild>
            <Link href={trackPagePath}>View order status</Link>
          </Button>
        </div>

        {/* Add booking to calendar */}
        <div className="mb-8 p-6 border border-border rounded-lg">
          <h3 className="font-semibold mb-2">Add booking to calendar</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Add this booking to your calendar so you don&apos;t miss it.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => downloadIcs(order!)}>
              Download .ics file
            </Button>
            <Button variant="outline" onClick={() => openGoogleCalendar(order!)}>
              Add to Google Calendar
            </Button>
          </div>
        </div>

        {/* Next steps: Create account / Login / New order */}
        <div className="mb-8 p-6 border border-border rounded-lg">
          <h3 className="font-semibold mb-3">What would you like to do next?</h3>

          {/* Option 1: Link to account (if guest and not linked) */}
          {(!isLinked && (order!.is_guest_order || order!.customer)) && (
            <div className="space-y-2 mb-4">
              {emailExists === true ? (
                <>
                  <p className="text-sm text-muted-foreground">
                    You already have an account with this email. Log in to link this order and manage your bookings.
                  </p>
                  <Button onClick={() => setShowLinkingModal(true)} className="w-full sm:w-auto">
                    Login & link order
                  </Button>
                </>
              ) : emailExists === false ? (
                <>
                  <p className="text-sm text-muted-foreground">
                    Create an account to link this order and manage future bookings in one place.
                  </p>
                  <Button onClick={() => setShowLinkingModal(true)} variant="default" className="w-full sm:w-auto">
                    Create account & link order
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    Create an account or log in to link this order and manage your bookings.
                  </p>
                  <Button onClick={() => setShowLinkingModal(true)} variant="default" className="w-full sm:w-auto">
                    Create account or login
                  </Button>
                </>
              )}
              <p className="text-xs text-muted-foreground pt-1">
                Optional — your order works without an account. You can link it later.
              </p>
            </div>
          )}

          {/* Option 2: Create new order (always shown) */}
          <div className="pt-3 border-t border-border">
            <p className="text-sm text-muted-foreground mb-2">Book another service</p>
            <Button
              variant="outline"
              className="w-full sm:w-auto"
              onClick={() => {
                resetBooking()
                router.push('/booking/postcode')
              }}
            >
              Create new order
            </Button>
          </div>
        </div>

        {/* Account Linked Success Message */}
        {!order!.is_guest_order || isLinked ? (
          <div className="mb-8 p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <h3 className="font-semibold mb-2 text-green-800 dark:text-green-200">
              ✓ Order Linked to Account
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300">
              This order is linked to your account. You can manage it from your dashboard.
            </p>
          </div>
        ) : null}

        {/* Account Linking Modal */}
        {!isLinked && (order!.guest_email || order!.customer?.email) && (
          <AccountLinkingModal
            orderNumber={order!.order_number}
            guestEmail={order!.guest_email || order!.customer?.email || ''}
            isOpen={showLinkingModal}
            onClose={() => setShowLinkingModal(false)}
            onSuccess={() => {
              setIsLinked(true)
              setShowLinkingModal(false)
              // Optionally refresh order data
              window.location.reload()
            }}
            emailExists={emailExists === true}
          />
        )}

        {/* Bottom actions: Return Home (Track order + Create new order are above) */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/"
            className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center inline-flex items-center justify-center"
          >
            Return Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function ConfirmationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-muted-foreground">Loading...</p></div>}>
      <ConfirmationPageContent />
    </Suspense>
  )
}
