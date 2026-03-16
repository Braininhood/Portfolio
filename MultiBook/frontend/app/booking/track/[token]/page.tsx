'use client'

/**
 * Guest order or subscription tracking by token (from email link).
 * Route: /booking/track/[token]
 * Tries order by token first, then subscription by token.
 */
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { Button } from '@/components/ui/button'

interface OrderData {
  id: number
  order_number: string
  status: string
  total_price: string
  scheduled_date: string
  scheduled_time?: string
  guest_email?: string
  guest_name?: string
  is_guest_order: boolean
  items?: Array<{ service_name?: string; quantity?: number }>
}

interface SubscriptionData {
  id: number
  subscription_number: string
  status: string
  total_price: string
  start_date: string
  end_date: string
  frequency: string
  duration_months: number
  total_appointments: number
  completed_appointments: number
  service?: { name?: string }
}

export default function TrackOrderPage() {
  const params = useParams()
  const token = typeof params?.token === 'string' ? params.token : null

  const [order, setOrder] = useState<OrderData | null>(null)
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError('Invalid tracking link')
      setLoading(false)
      return
    }

    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const orderRes = await apiClient.get(PUBLIC_ENDPOINTS.BOOKINGS.GUEST_ORDER_TRACK(token))
        if (cancelled) return
        if (orderRes.data.success && orderRes.data.data) {
          setOrder(orderRes.data.data)
          setSubscription(null)
          setLoading(false)
          return
        }
      } catch {
        // Not an order; try subscription
      }
      try {
        const subRes = await apiClient.get(PUBLIC_ENDPOINTS.BOOKINGS.GUEST_SUBSCRIPTION_TRACK(token))
        if (cancelled) return
        if (subRes.data.success && subRes.data.data) {
          setSubscription(subRes.data.data)
          setOrder(null)
          setLoading(false)
          return
        }
      } catch {
        // ignore
      }
      if (!cancelled) {
        setError('Order or subscription not found')
      }
      setLoading(false)
    }
    run()
    return () => { cancelled = true }
  }, [token])

  if (loading) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto text-center min-h-[300px] flex items-center justify-center">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (error || (!order && !subscription)) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="p-6 bg-destructive/10 text-destructive rounded-lg mb-6">
            {error || 'Order or subscription not found'}
          </div>
          <Button asChild variant="outline">
            <Link href="/booking/postcode">Start a new booking</Link>
          </Button>
        </div>
      </div>
    )
  }

  if (subscription) {
    const freqLabel = subscription.frequency === 'weekly' ? 'Every week' : subscription.frequency === 'biweekly' ? 'Every 2 weeks' : 'Every month'
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-2xl font-bold mb-6">Your subscription status</h1>
          <div className="mb-6 p-6 border border-border rounded-lg">
            <div className="flex justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm text-muted-foreground">Subscription number</p>
                <p className="font-mono font-semibold">{subscription.subscription_number}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Status</p>
                <p className="font-medium capitalize">{subscription.status}</p>
              </div>
            </div>
          </div>
          <div className="mb-6 p-6 border border-border rounded-lg space-y-3">
            <h2 className="font-semibold">Details</h2>
            {subscription.service?.name && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Service</span>
                <span className="font-medium">{subscription.service.name}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Frequency</span>
              <span className="font-medium">{freqLabel}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{subscription.completed_appointments} / {subscription.total_appointments} visits</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Total</span>
              <span className="font-medium">£{parseFloat(subscription.total_price).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Start date</span>
              <span>
                {new Date(subscription.start_date).toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="outline">
              <Link href="/cus/subscriptions">My Subscriptions</Link>
            </Button>
            <Button asChild>
              <Link href="/booking/postcode">Book another service</Link>
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (!order) {
    return null
  }

  const statusLabel =
    order.status === 'confirmed'
      ? 'Confirmed'
      : order.status === 'completed'
        ? 'Completed'
        : order.status === 'cancelled'
          ? 'Cancelled'
          : order.status === 'pending'
            ? 'Pending'
            : order.status

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Your order status</h1>

        <div className="mb-6 p-6 border border-border rounded-lg">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-sm text-muted-foreground">Order number</p>
              <p className="font-mono font-semibold">{order.order_number}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Status</p>
              <p className="font-medium capitalize">{statusLabel}</p>
            </div>
          </div>
        </div>

        <div className="mb-6 p-6 border border-border rounded-lg space-y-3">
          <h2 className="font-semibold">Details</h2>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Total</span>
            <span className="font-medium">£{parseFloat(order.total_price).toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Date</span>
            <span>
              {new Date(order.scheduled_date).toLocaleDateString('en-GB', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
          {order.scheduled_time && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Time</span>
              <span>
                {new Date(`2000-01-01T${order.scheduled_time}`).toLocaleTimeString(
                  'en-GB',
                  { hour: '2-digit', minute: '2-digit' }
                )}
              </span>
            </div>
          )}
          {order.items?.length ? (
            <div className="pt-2 border-t border-border">
              <p className="text-sm text-muted-foreground mb-1">Services</p>
              <ul className="text-sm">
                {order.items.map((item, i) => (
                  <li key={i}>
                    {item.service_name || 'Service'} {item.quantity && item.quantity > 1 ? `× ${item.quantity}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          This link was sent to your email. You can use it anytime to check your order status.
        </p>

        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href={`/booking/confirmation?order=${encodeURIComponent(order.order_number)}`}>
              View full confirmation
            </Link>
          </Button>
          <Button asChild>
            <Link href="/booking/postcode">Book another service</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
