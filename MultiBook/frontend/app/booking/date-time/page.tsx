'use client'

/**
 * Booking Step 3: Date & Time Selection
 * Route: /booking/date-time (Public - Guest Checkout)
 * 
 * Calendar and time slot selection for booking.
 */
import { useBookingStore } from '@/store/booking-store'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { formatDate } from '@/lib/utils'
import { addDays, format, addWeeks, subWeeks, isSameDay, isSameMonth, isPast, startOfMonth, endOfMonth, eachDayOfInterval, isToday, startOfWeek, endOfWeek } from 'date-fns'

interface TimeSlot {
  time: string
  available: boolean
  staff_ids?: number[]
  reason?: string
}

export default function DateTimePage() {
  const router = useRouter()
  const { postcode, selectedService, setDateAndTime, bookingType } = useBookingStore()
  const isSubscription = bookingType === 'subscription'
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [slots, setSlots] = useState<TimeSlot[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentMonth, setCurrentMonth] = useState(new Date())

  useEffect(() => {
    if (!postcode || !selectedService) {
      router.push('/booking/postcode')
      return
    }
  }, [postcode, selectedService, router])

  useEffect(() => {
    if (selectedDate) {
      fetchAvailableSlots(selectedDate)
    } else {
      setSlots([])
      setSelectedSlot(null)
    }
  }, [selectedDate, postcode, selectedService])

  const fetchAvailableSlots = async (date: Date) => {
    if (!postcode || !selectedService) return

    setLoading(true)
    setError(null)
    setSelectedSlot(null)

    try {
      const dateStr = format(date, 'yyyy-MM-dd')
      const response = await apiClient.get(PUBLIC_ENDPOINTS.SLOTS.AVAILABLE, {
        params: {
          postcode,
          service_id: selectedService,
          date: dateStr,
        },
      })

      if (response.data.success && response.data.data) {
        setSlots(response.data.data.slots || [])
      } else {
        setError(response.data.error?.message || 'Failed to load available slots')
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error?.message || 
                          'Unable to load available time slots. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleDateSelect = (date: Date) => {
    if (isPast(date) && !isToday(date)) {
      return // Can't select past dates
    }
    setSelectedDate(date)
  }

  const handleSlotSelect = (time: string) => {
    setSelectedSlot(time)
  }

  const handleContinue = () => {
    if (selectedDate && selectedSlot) {
      setDateAndTime(
        format(selectedDate, 'yyyy-MM-dd'),
        selectedSlot,
        undefined // Staff will be selected automatically
      )
      router.push('/booking/details')
    }
  }

  // Calendar helpers
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 }) // Monday
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })

  const calendarDays = eachDayOfInterval({
    start: calendarStart,
    end: calendarEnd,
  })

  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const _availableSlots = slots.filter(slot => slot.available)
  const _unavailableSlots = slots.filter(slot => !slot.available)
  const formatTimeDisplay = (time: string) => {
    const [hours, minutes] = time.split(':').map(Number)
    const period = hours >= 12 ? 'PM' : 'AM'
    const hours12 = hours % 12 || 12
    return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            {isSubscription ? 'Select start date' : 'Select Date & Time'}
          </h1>
          <p className="text-muted-foreground">
            {isSubscription
              ? 'Choose the start date for your subscription (and preferred time for the first visit)'
              : 'Choose your preferred date and time slot for your booking'}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Calendar */}
          <div>
            <div className="border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={() => setCurrentMonth(subWeeks(currentMonth, 4))}
                  className="p-2 hover:bg-muted rounded"
                >
                  ←
                </button>
                <h2 className="text-xl font-semibold">
                  {format(currentMonth, 'MMMM yyyy')}
                </h2>
                <button
                  onClick={() => setCurrentMonth(addWeeks(currentMonth, 4))}
                  className="p-2 hover:bg-muted rounded"
                >
                  →
                </button>
              </div>

              <div className="grid grid-cols-7 gap-1 mb-2">
                {weekDays.map((day) => (
                  <div key={day} className="text-center text-sm font-medium text-muted-foreground py-2">
                    {day}
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((day, idx) => {
                  const isCurrentMonth = isSameMonth(day, currentMonth)
                  const isSelected = selectedDate && isSameDay(day, selectedDate)
                  const isTodayDate = isToday(day)
                  const isPastDate = isPast(day) && !isTodayDate

                  return (
                    <button
                      key={idx}
                      onClick={() => handleDateSelect(day)}
                      disabled={isPastDate}
                      className={`
                        aspect-square p-2 rounded text-sm transition-colors
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
            <div className="border border-border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">
                {selectedDate ? formatDate(selectedDate, 'long') : 'Select a date'}
              </h2>

              {loading ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">Loading available slots...</p>
                </div>
              ) : !selectedDate ? (
                <p className="text-muted-foreground">Please select a date to see available time slots.</p>
              ) : slots.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">
                    No time slots for this date (outside staff hours).
                  </p>
                  <button
                    onClick={() => {
                      setCurrentMonth(addDays(selectedDate, 1))
                      setSelectedDate(null)
                    }}
                    className="text-primary hover:underline"
                  >
                    Try another date
                  </button>
                </div>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground mb-2">
                    Available slots are selectable; grey slots are unavailable (e.g. already booked or service in progress).
                  </p>
                  <div className="grid grid-cols-3 gap-2 mb-2">
                    {slots.map((slot) => (
                      <button
                        key={slot.time}
                        type="button"
                        onClick={() => slot.available && handleSlotSelect(slot.time)}
                        disabled={!slot.available}
                        className={`
                          p-3 rounded-lg border transition-colors text-sm font-medium
                          ${!slot.available
                            ? 'bg-muted/60 text-muted-foreground border-muted cursor-not-allowed line-through'
                            : selectedSlot === slot.time
                              ? 'bg-primary text-primary-foreground border-primary'
                              : 'border-border hover:border-primary hover:bg-muted'
                          }
                        `}
                        title={!slot.available ? (slot.reason || 'Unavailable') : undefined}
                      >
                        {formatTimeDisplay(slot.time)}
                        {!slot.available && (
                          <span className="block text-xs mt-0.5 font-normal opacity-80">
                            {slot.reason || 'Unavailable'}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>

                  {selectedSlot && (
                    <button
                      onClick={handleContinue}
                      className="w-full py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium mt-4"
                    >
                      Continue to Next Step
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-4">
          <button
            onClick={() => router.push('/booking/services')}
            className="px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors"
          >
            ← Back to Services
          </button>
        </div>
      </div>
    </div>
  )
}
