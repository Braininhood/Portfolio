'use client'

/**
 * Booking Step 6: Payment
 * Route: /booking/payment (Public - Guest Checkout)
 * 
 * Basic payment page for guest checkout.
 * For Week 3, this is a placeholder - actual payment integration will be in later weeks.
 */
import { useBookingStore } from '@/store/booking-store'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { formatCurrency } from '@/lib/utils'
import { CouponInput } from '@/components/booking/CouponInput'

export default function PaymentPage() {
  const router = useRouter()
  const {
    postcode,
    selectedService,
    selectedDate,
    selectedTime,
    selectedStaff,
    guestName,
    guestEmail,
    guestPhone,
    address,
    notes,
    customerId,
    bookingType,
    subscriptionFrequency,
    subscriptionDuration,
  } = useBookingStore()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [_orderData, setOrderData] = useState<unknown>(null)
  const [serviceDetails, setServiceDetails] = useState<{
    name: string
    price: number
    duration: number
    category_name?: string
  } | null>(null)
  const [loadingService, setLoadingService] = useState(true)
  const [appliedCoupon, setAppliedCoupon] = useState<{
    code: string
    discountAmount: string
    finalAmount: string
  } | null>(null)

  const isSubscription = bookingType === 'subscription'

  useEffect(() => {
    // Redirect if required data is missing
    if (!postcode || !selectedService || !guestEmail || !address) {
      router.push('/booking/details')
      return
    }
    if (isSubscription) {
      if (!subscriptionFrequency || !subscriptionDuration) {
        router.push('/booking/subscription-options')
        return
      }
      if (!selectedDate) {
        router.push('/booking/date-time')
        return
      }
      // Subscription: time slot optional for start date
    } else {
      if (!selectedDate || !selectedTime) {
        router.push('/booking/date-time')
        return
      }
    }

    // Fetch service details
    const fetchServiceDetails = async () => {
      if (!selectedService) return

      setLoadingService(true)
      try {
        const response = await apiClient.get(`${PUBLIC_ENDPOINTS.SERVICES.LIST}${selectedService}/`)
        
        if (response.data.success && response.data.data) {
          const service = response.data.data
          setServiceDetails({
            name: service.name,
            price: typeof service.price === 'string' ? parseFloat(service.price) : service.price,
            duration: service.duration,
            category_name: service.category_name || service.category?.name,
          })
        }
      } catch (err: any) {
        console.error('Failed to fetch service details:', err)
      } finally {
        setLoadingService(false)
      }
    }

    fetchServiceDetails()
  }, [postcode, selectedService, selectedDate, selectedTime, guestEmail, address, router, isSubscription, subscriptionFrequency, subscriptionDuration])

  const handleCreateOrder = async () => {
    if (!selectedService || !selectedDate || !selectedTime || !guestEmail || !address) {
      setError('Missing required booking information')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Parse date and time
      const [_year, _month, _day] = selectedDate.split('-').map(Number)
      const [hours, minutes] = selectedTime.split(':').map(Number)

      // Create order (send customer_id when logged-in customer so order is linked and has full info)
      const payload: Record<string, unknown> = {
        items: [
          {
            service_id: selectedService,
            quantity: 1,
            staff_id: selectedStaff || null,
          },
        ],
        scheduled_date: selectedDate,
        scheduled_time: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`,
        guest_email: guestEmail,
        guest_name: guestName || '',
        guest_phone: guestPhone || '',
        address_line1: address.line1,
        address_line2: address.line2 || '',
        city: address.city,
        postcode: address.postcode,
        country: address.country || 'United Kingdom',
        notes: notes || '',
        coupon_code: appliedCoupon?.code || '',
      }
      if (customerId) payload.customer_id = customerId

      const response = await apiClient.post(PUBLIC_ENDPOINTS.BOOKINGS.ORDER, payload)

      if (response.data.success) {
        const data = response.data.data
        const meta = response.data.meta
        setOrderData(data)
        
        // Order number: meta first (from create response), then serialized data
        const orderNumber = meta?.order_number ?? data?.order_number
        if (!orderNumber) {
          setError('Order created but order number not found. Please contact support.')
          return
        }
        const confirmationUrl = `/booking/confirmation?order=${encodeURIComponent(orderNumber)}`
        // Full page navigation so confirmation page loads with correct URL (no flash/redirect)
        window.location.href = confirmationUrl
      } else {
        setError(response.data.error?.message || 'Failed to create order')
      }
    } catch (err: any) {
      console.error('Order creation error:', err)
      const errorMessage = err.response?.data?.error?.message || 
                          'Unable to create order. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSubscription = async () => {
    if (!selectedService || !selectedDate || !guestEmail || !address || !subscriptionFrequency || !subscriptionDuration || !serviceDetails) {
      setError('Missing required subscription information')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const payload: Record<string, unknown> = {
        service_id: selectedService,
        staff_id: selectedStaff || null,
        frequency: subscriptionFrequency,
        duration_months: subscriptionDuration,
        start_date: selectedDate,
        price_per_appointment: String(serviceDetails.price),
        guest_email: guestEmail,
        guest_name: guestName || '',
        guest_phone: guestPhone || '',
        address_line1: address.line1,
        address_line2: address.line2 || '',
        city: address.city,
        postcode: address.postcode,
        country: address.country || 'United Kingdom',
      }
      if (customerId) payload.customer_id = customerId

      const response = await apiClient.post(PUBLIC_ENDPOINTS.BOOKINGS.SUBSCRIPTIONS_CREATE, payload)

      if (response.data.success) {
        const data = response.data.data
        const meta = response.data.meta
        const subscriptionNumber = meta?.subscription_number ?? data?.subscription_number
        if (!subscriptionNumber) {
          setError('Subscription created but subscription number not found. Please contact support.')
          return
        }
        const confirmationUrl = `/booking/confirmation?subscription=${encodeURIComponent(subscriptionNumber)}`
        window.location.href = confirmationUrl
      } else {
        setError(response.data.error?.message || 'Failed to create subscription')
      }
    } catch (err: any) {
      console.error('Subscription creation error:', err)
      const errorMessage = err.response?.data?.error?.message ||
        'Unable to create subscription. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Calculate total from service price
  const pricePerVisit = serviceDetails?.price ?? 0
  const subtotal = pricePerVisit
  const discount = appliedCoupon ? parseFloat(appliedCoupon.discountAmount) : 0
  const total = subtotal - discount

  // Subscription: total visits and total price (backend uses same formula)
  const subscriptionVisitsPerMonth =
    subscriptionFrequency === 'weekly' ? 4
      : subscriptionFrequency === 'biweekly' ? 2
        : subscriptionFrequency === 'monthly' ? 1 : 0
  const subscriptionTotalVisits = (subscriptionDuration ?? 0) * subscriptionVisitsPerMonth
  const subscriptionTotalPrice = subscriptionTotalVisits * pricePerVisit
  const frequencyLabel =
    subscriptionFrequency === 'weekly' ? 'Every week'
      : subscriptionFrequency === 'biweekly' ? 'Every 2 weeks'
        : subscriptionFrequency === 'monthly' ? 'Every month' : ''

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            {isSubscription ? 'Review & Confirm Subscription' : 'Review & Confirm'}
          </h1>
          <p className="text-muted-foreground">
            {isSubscription
              ? 'Review your subscription details and confirm'
              : 'Review your booking details and confirm your order'}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">
            {error}
          </div>
        )}

        {/* Booking Summary */}
        <div className="mb-8 p-6 border border-border rounded-lg space-y-4">
          <h2 className="text-xl font-semibold">Booking Summary</h2>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Service:</span>
              <span className="font-medium text-right">
                {loadingService ? (
                  'Loading...'
                ) : serviceDetails ? (
                  <>
                    {serviceDetails.category_name && (
                      <span className="text-xs text-muted-foreground block">{serviceDetails.category_name}</span>
                    )}
                    <span>{serviceDetails.name}</span>
                    <span className="text-sm text-muted-foreground block mt-1">
                      {serviceDetails.duration} minutes
                    </span>
                  </>
                ) : (
                  `Service ID ${selectedService}`
                )}
              </span>
            </div>
            {serviceDetails && (
              <>
                <div className="flex justify-between pt-2 border-t border-border">
                  <span className="text-muted-foreground">
                    {isSubscription ? 'Price per visit:' : 'Price:'}
                  </span>
                  <span className="font-medium">{formatCurrency(serviceDetails.price)}</span>
                </div>
                {isSubscription && subscriptionFrequency && subscriptionDuration && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Frequency:</span>
                      <span className="font-medium">{frequencyLabel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="font-medium">{subscriptionDuration} month{subscriptionDuration !== 1 ? 's' : ''}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total visits:</span>
                      <span className="font-medium">{subscriptionTotalVisits} visits</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Subscription total:</span>
                      <span className="font-medium">{formatCurrency(subscriptionTotalPrice)}</span>
                    </div>
                  </>
                )}
              </>
            )}
            <div className="flex justify-between">
              <span className="text-muted-foreground">{isSubscription ? 'Start date:' : 'Date:'}</span>
              <span className="font-medium">
                {selectedDate && new Date(selectedDate).toLocaleDateString('en-GB', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
            {!isSubscription && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time:</span>
                <span className="font-medium">{selectedTime}</span>
              </div>
            )}
            {address && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Address:</span>
                <span className="font-medium text-right">
                  {address.line1}, {address.city}, {address.postcode}
                </span>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-border space-y-2">
            {!isSubscription && (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal:</span>
                  <span>{formatCurrency(subtotal)}</span>
                </div>
                {appliedCoupon && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount ({appliedCoupon.code}):</span>
                    <span>-{formatCurrency(discount)}</span>
                  </div>
                )}
              </>
            )}
            <div className="flex justify-between text-lg font-bold pt-2 border-t border-border">
              <span>{isSubscription ? 'Total:' : 'Total:'}</span>
              <span>{formatCurrency(isSubscription ? subscriptionTotalPrice : total)}</span>
            </div>
          </div>
        </div>

        {/* Coupon Input - order only (subscription create API doesn't support coupon yet) */}
        {!isSubscription && (
          <div className="mb-8 p-6 border border-border rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Have a Coupon Code?</h2>
            <CouponInput
              orderAmount={subtotal}
              serviceIds={selectedService ? [selectedService] : []}
              onCouponApplied={setAppliedCoupon}
              onCouponRemoved={() => setAppliedCoupon(null)}
              appliedCoupon={appliedCoupon}
            />
          </div>
        )}


        {/* Customer Information */}
        <div className="mb-8 p-6 border border-border rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-muted-foreground">Name:</span>{' '}
              <span className="font-medium">{guestName}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Email:</span>{' '}
              <span className="font-medium">{guestEmail}</span>
            </div>
            {guestPhone && (
              <div>
                <span className="text-muted-foreground">Phone:</span>{' '}
                <span className="font-medium">{guestPhone}</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => router.back()}
            disabled={loading}
            className="flex-1 px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
          >
            Back
          </button>
          {isSubscription ? (
            <button
              type="button"
              onClick={handleCreateSubscription}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold disabled:opacity-50"
            >
              {loading ? 'Creating Subscription...' : 'Complete Subscription'}
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCreateOrder}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold disabled:opacity-50"
            >
              {loading ? 'Creating Order...' : 'Complete Booking'}
            </button>
          )}
        </div>

        {/* Info */}
        <div className="mt-8 p-6 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground">
            {isSubscription ? (
              <>
                <strong>Note:</strong> Your subscription will be created and you&apos;ll receive a confirmation with your subscription number and tracking link.
                You can manage or pause it from My Subscriptions when logged in.
              </>
            ) : (
              <>
                <strong>Note:</strong> Your order will be created and you&apos;ll receive a confirmation email with your order number and tracking link.
                Payment will be processed through your account after order confirmation.
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
