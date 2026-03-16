'use client'

/**
 * Booking: Subscription options (frequency + duration)
 * Route: /booking/subscription-options (Public - Guest Checkout)
 *
 * Shown after user selects "Subscribe" on a service.
 * Choose: weekly / every 2 weeks / monthly, and duration 1–12 months.
 */
import { useBookingStore } from '@/store/booking-store'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

const FREQUENCIES = [
  { value: 'weekly' as const, label: 'Every week' },
  { value: 'biweekly' as const, label: 'Every 2 weeks' },
  { value: 'monthly' as const, label: 'Every month' },
]

const DURATIONS = Array.from({ length: 12 }, (_, i) => i + 1)

export default function SubscriptionOptionsPage() {
  const router = useRouter()
  const { postcode, selectedService, setSubscriptionDetails } = useBookingStore()
  const [frequency, setFrequency] = useState<'weekly' | 'biweekly' | 'monthly'>('weekly')
  const [duration, setDuration] = useState(3)

  useEffect(() => {
    if (!postcode || !selectedService) {
      router.push('/booking/postcode')
      return
    }
  }, [postcode, selectedService, router])

  const handleContinue = () => {
    setSubscriptionDetails(frequency, duration)
    router.push('/booking/date-time')
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Subscription options</h1>
          <p className="text-muted-foreground">
            How often should we come, and for how long?
          </p>
        </div>

        <div className="space-y-8">
          <div>
            <h2 className="text-lg font-semibold mb-4">Frequency</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {FREQUENCIES.map((f) => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => setFrequency(f.value)}
                  className={`px-4 py-4 rounded-lg border-2 text-left transition-colors ${
                    frequency === f.value
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <span className="font-medium">{f.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold mb-4">Duration</h2>
            <p className="text-sm text-muted-foreground mb-3">
              How many months? (1–12)
            </p>
            <div className="flex flex-wrap gap-2">
              {DURATIONS.map((months) => (
                <button
                  key={months}
                  type="button"
                  onClick={() => setDuration(months)}
                  className={`w-12 h-12 rounded-lg border-2 font-medium transition-colors ${
                    duration === months
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {months}
                </button>
              ))}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {duration} month{duration !== 1 ? 's' : ''} selected
            </p>
          </div>
        </div>

        <div className="mt-10 flex gap-4">
          <button
            type="button"
            onClick={() => router.push('/booking/services')}
            className="px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            Back to services
          </button>
          <button
            type="button"
            onClick={handleContinue}
            className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold"
          >
            Continue – choose start date
          </button>
        </div>
      </div>
    </div>
  )
}
