'use client'

/**
 * Booking Step 4: Booking Type Selection
 * Route: /booking/booking-type (Public - Guest Checkout)
 * 
 * Options:
 * - Single Appointment
 * - Subscription (weekly/biweekly/monthly for 1-12 months)
 * - Order (multiple services)
 */
export default function BookingTypePage() {
  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <h1 className="text-3xl font-bold mb-8">Choose Booking Type</h1>
      <div className="space-y-4">
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Single Appointment</h3>
          <p className="text-muted-foreground">One-time service booking</p>
        </div>
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Subscription</h3>
          <p className="text-muted-foreground">
            Recurring service (weekly/biweekly/monthly for 1-12 months)
          </p>
        </div>
        <div className="p-6 border rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Order (Multiple Services)</h3>
          <p className="text-muted-foreground">
            Request multiple services in one order (e.g., window cleaning + grass cutting)
          </p>
        </div>
      </div>
      <p className="mt-8 text-muted-foreground">
        Booking type selection will be implemented in Week 3 (for single appointments) and Week 9 (for subscriptions/orders).
      </p>
    </div>
  )
}
