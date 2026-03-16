'use client'

/**
 * Booking Home/Entry Point
 * Route: /booking (Public - Guest Checkout)
 * 
 * Redirects to postcode entry (first step of booking flow).
 */
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function BookingPage() {
  const router = useRouter()

  useEffect(() => {
    router.push('/booking/postcode')
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-muted-foreground">Redirecting to booking...</p>
      </div>
    </div>
  )
}
