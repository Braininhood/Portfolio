'use client'

/**
 * Booking Step 1: Postcode Entry
 * Route: /booking/postcode (Public - Guest Checkout)
 * 
 * This is the first step of the booking flow.
 * No login/registration required.
 */
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useBookingStore } from '@/store/booking-store'
import { validateUKPostcode, formatPostcode } from '@/lib/utils'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'

export default function PostcodePage() {
  const router = useRouter()
  const { postcode, setPostcode } = useBookingStore()
  const [inputValue, setInputValue] = useState(postcode || '')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const formatted = formatPostcode(inputValue)
    
    // First, validate UK postcode format on client side
    if (!validateUKPostcode(formatted)) {
      setError('Please enter a valid UK postcode (e.g., SW1A 1AA). MultiBook currently operates only in the UK.')
      setLoading(false)
      return
    }

    try {
      // Validate postcode with backend API (checks format + UK location via Google Maps)
      const response = await apiClient.get(PUBLIC_ENDPOINTS.SERVICES.BY_POSTCODE, {
        params: { postcode: formatted }
      })

      if (response.data.success) {
        // Postcode is valid and services are available (even if count is 0)
        setPostcode(formatted)
        router.push('/booking/services')
      } else {
        // Handle error from API
        const errorMessage = response.data.error?.message || 'Invalid postcode. Please try again.'
        setError(errorMessage)
      }
    } catch (err: any) {
      // Handle API errors
      const errorMessage = err.response?.data?.error?.message || 
                          'Unable to validate postcode. Please check your connection and try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Book Your Service</h1>
          <p className="text-muted-foreground mb-2">
            Enter your UK postcode to see available services in your area
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <span className="text-sm text-blue-800 dark:text-blue-200">
              🇬🇧 MultiBook currently operates only in the UK
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="postcode" className="block text-sm font-medium mb-2">
              Your Postcode
            </label>
            <input
              id="postcode"
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value.toUpperCase())}
              placeholder="e.g., SW1A 1AA"
              required
              className="w-full px-4 py-3 text-lg border border-border rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
              autoFocus
            />
            <p className="mt-2 text-sm text-muted-foreground">
              We&apos;ll show you services available in your UK area
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Validating...' : 'Continue'}
          </button>
        </form>

        <div className="text-center text-sm text-muted-foreground">
          <p>
            <span className="font-medium">No login required!</span> You can book as a guest.
          </p>
        </div>
      </div>
    </div>
  )
}
