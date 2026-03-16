'use client'

/**
 * Calendar + time slot picker (same UX as /booking/date-time).
 * Used on admin order and appointment edit pages.
 */
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { formatDate } from '@/lib/utils'
import { addWeeks, subWeeks, isSameDay, isSameMonth, isPast, startOfMonth, endOfMonth, eachDayOfInterval, isToday, startOfWeek, endOfWeek, format } from 'date-fns'

interface TimeSlot {
  time: string
  available: boolean
  staff_ids?: number[]
  reason?: string
}

interface DateTimeSlotPickerProps {
  postcode: string
  serviceId: number
  staffId?: number | null
  selectedDate: string // yyyy-MM-dd
  selectedTime: string // HH:MM
  onSelect: (date: string, time: string) => void
  disabled?: boolean
}

function formatTimeDisplay(time: string) {
  const [hours, minutes] = time.split(':').map(Number)
  const period = hours >= 12 ? 'PM' : 'AM'
  const hours12 = hours % 12 || 12
  return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`
}

export function DateTimeSlotPicker({
  postcode,
  serviceId,
  staffId,
  selectedDate,
  selectedTime,
  onSelect,
  disabled,
}: DateTimeSlotPickerProps) {
  const [selectedDateObj, setSelectedDateObj] = useState<Date | null>(
    selectedDate ? new Date(selectedDate + 'T12:00:00') : null
  )
  const [slots, setSlots] = useState<TimeSlot[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentMonth, setCurrentMonth] = useState(
    selectedDate ? new Date(selectedDate + 'T12:00:00') : new Date()
  )

  useEffect(() => {
    if (selectedDate) {
      const d = new Date(selectedDate + 'T12:00:00')
      setSelectedDateObj(d)
      setCurrentMonth(d)
    } else {
      setSelectedDateObj(null)
    }
  }, [selectedDate])

  useEffect(() => {
    if (!selectedDateObj || !postcode.trim() || !serviceId) {
      setSlots([])
      return
    }
    const dateStr = format(selectedDateObj, 'yyyy-MM-dd')
    setLoading(true)
    setError(null)
    const params: Record<string, string | number> = {
      postcode: postcode.trim(),
      service_id: serviceId,
      date: dateStr,
    }
    if (staffId) params.staff_id = staffId
    apiClient
      .get(PUBLIC_ENDPOINTS.SLOTS.AVAILABLE, { params })
      .then((res) => {
        if (res.data?.success && res.data?.data?.slots) {
          setSlots(res.data.data.slots)
        } else {
          setSlots([])
        }
      })
      .catch((err) => {
        setError(err.response?.data?.error?.message || 'Failed to load slots')
        setSlots([])
      })
      .finally(() => setLoading(false))
  }, [selectedDateObj, postcode, serviceId, staffId])

  const handleDateSelect = (date: Date) => {
    if (isPast(date) && !isToday(date)) return
    setSelectedDateObj(date)
    onSelect(format(date, 'yyyy-MM-dd'), '')
  }

  const handleSlotSelect = (time: string) => {
    if (!selectedDateObj) return
    onSelect(format(selectedDateObj, 'yyyy-MM-dd'), time)
  }

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            type="button"
            onClick={() => setCurrentMonth(subWeeks(currentMonth, 4))}
            className="p-2 hover:bg-muted rounded disabled:opacity-50"
            disabled={disabled}
          >
            ←
          </button>
          <span className="text-lg font-semibold">{format(currentMonth, 'MMMM yyyy')}</span>
          <button
            type="button"
            onClick={() => setCurrentMonth(addWeeks(currentMonth, 4))}
            className="p-2 hover:bg-muted rounded disabled:opacity-50"
            disabled={disabled}
          >
            →
          </button>
        </div>
        <div className="grid grid-cols-7 gap-1 mb-2">
          {weekDays.map((day) => (
            <div key={day} className="text-center text-xs font-medium text-muted-foreground py-1">
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {calendarDays.map((day, idx) => {
            const isCurrentMonth = isSameMonth(day, currentMonth)
            const isSelected = selectedDateObj && isSameDay(day, selectedDateObj)
            const isTodayDate = isToday(day)
            const isPastDate = isPast(day) && !isTodayDate
            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleDateSelect(day)}
                disabled={isPastDate || disabled}
                className={`
                  aspect-square p-1 rounded text-sm transition-colors
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

      <div className="border border-border rounded-lg p-4">
        <h3 className="font-semibold mb-2">
          {selectedDateObj ? formatDate(selectedDateObj, 'long') : 'Select a date'}
        </h3>
        {error && (
          <p className="text-sm text-destructive mb-2">{error}</p>
        )}
        {loading ? (
          <p className="text-muted-foreground text-sm">Loading available slots…</p>
        ) : !selectedDateObj ? (
          <p className="text-muted-foreground text-sm">Select a date to see time slots.</p>
        ) : slots.length === 0 ? (
          <p className="text-muted-foreground text-sm">No slots for this date.</p>
        ) : (
          <>
            <p className="text-xs text-muted-foreground mb-2">Choose a time (available slots only).</p>
            <div className="grid grid-cols-3 gap-2">
              {slots.map((slot) => (
                <button
                  key={slot.time}
                  type="button"
                  onClick={() => slot.available && handleSlotSelect(slot.time)}
                  disabled={!slot.available || disabled}
                  className={`
                    p-2 rounded-lg border text-sm font-medium transition-colors
                    ${!slot.available
                      ? 'bg-muted/60 text-muted-foreground border-muted cursor-not-allowed'
                      : selectedTime === slot.time
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'border-border hover:border-primary hover:bg-muted'
                    }
                  `}
                >
                  {formatTimeDisplay(slot.time)}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
