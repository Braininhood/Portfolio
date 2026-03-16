'use client'

/**
 * Customer Calendar Widget
 * Shows upcoming appointments in a calendar view for the customer dashboard.
 */
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment } from '@/types/appointment'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export function CustomerCalendarWidget() {
  const router = useRouter()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      // Get next 30 days of appointments
      const dateTo = new Date(today)
      dateTo.setDate(dateTo.getDate() + 30)
      
      const params = new URLSearchParams({
        date_from: today.toISOString(),
        date_to: dateTo.toISOString(),
        status: 'pending,confirmed,in_progress',
      })
      
      const response = await apiClient.get(
        `${CUSTOMER_ENDPOINTS.APPOINTMENTS.LIST}?${params.toString()}`
      )
      
      const raw = response.data as { success?: boolean; data?: Appointment[]; results?: Appointment[] }
      const list = raw.results ?? raw.data ?? []
      if (Array.isArray(list)) {
        setAppointments(list.sort((a, b) => 
          new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        ))
      }
    } catch (err) {
      console.error('Error fetching appointments:', err)
    } finally {
      setLoading(false)
    }
  }

  // Get current month's days
  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startingDayOfWeek = firstDay.getDay()

  // Get appointments for a specific date
  const getAppointmentsForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0]
    return appointments.filter(apt => {
      const aptDate = new Date(apt.start_time).toISOString().split('T')[0]
      return aptDate === dateStr
    })
  }

  // Navigate months
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1))
  }

  const goToNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1))
  }

  const goToToday = () => {
    setCurrentDate(new Date())
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const today = new Date()
  const isToday = (date: Date) => {
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear()
  }

  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  if (loading) {
    return (
      <div className="bg-card border rounded-lg p-4">
        <div className="text-sm text-muted-foreground">Loading calendar...</div>
      </div>
    )
  }

  return (
    <div className="bg-card border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Calendar</h3>
          <p className="text-xs text-muted-foreground mt-1">
            Your upcoming appointments
          </p>
        </div>
        <Link href="/cus/bookings">
          <button className="text-sm text-primary hover:underline">
            View All →
          </button>
        </Link>
      </div>

      {/* Month Navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={goToPreviousMonth}
          className="p-1 hover:bg-muted rounded"
          aria-label="Previous month"
        >
          ←
        </button>
        <div className="flex items-center gap-2">
          <h4 className="font-semibold">
            {monthNames[month]} {year}
          </h4>
          <button
            onClick={goToToday}
            className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Today
          </button>
        </div>
        <button
          onClick={goToNextMonth}
          className="p-1 hover:bg-muted rounded"
          aria-label="Next month"
        >
          →
        </button>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {dayNames.map(day => (
          <div key={day} className="text-xs font-medium text-center text-muted-foreground py-1">
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {/* Empty cells for days before month starts */}
        {Array.from({ length: startingDayOfWeek }).map((_, i) => (
          <div key={`empty-${i}`} className="aspect-square" />
        ))}

        {/* Days of the month */}
        {Array.from({ length: daysInMonth }).map((_, i) => {
          const date = new Date(year, month, i + 1)
          const dayAppointments = getAppointmentsForDate(date)
          const isCurrentDay = isToday(date)
          
          return (
            <div
              key={i}
              className={`aspect-square border rounded p-1 text-xs cursor-pointer hover:bg-muted/50 transition-colors ${
                isCurrentDay ? 'bg-primary/10 border-primary' : 'border-border'
              }`}
              onClick={() => {
                if (dayAppointments.length > 0) {
                  router.push(`/cus/bookings/${dayAppointments[0].id}`)
                }
              }}
            >
              <div className={`text-center mb-1 ${isCurrentDay ? 'font-bold text-primary' : ''}`}>
                {i + 1}
              </div>
              {dayAppointments.length > 0 && (
                <div className="space-y-0.5">
                  {dayAppointments.slice(0, 2).map(apt => (
                    <div
                      key={apt.id}
                      className={`text-[10px] px-1 py-0.5 rounded truncate ${
                        apt.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                        apt.status === 'in_progress' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}
                      title={`${apt.service?.name || 'Service'} at ${formatTime(apt.start_time)}`}
                    >
                      {formatTime(apt.start_time)}
                    </div>
                  ))}
                  {dayAppointments.length > 2 && (
                    <div className="text-[10px] text-muted-foreground text-center">
                      +{dayAppointments.length - 2}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Upcoming Appointments List */}
      {appointments.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <h4 className="text-sm font-semibold mb-2">Upcoming</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {appointments.slice(0, 5).map(apt => (
              <div
                key={apt.id}
                className="flex items-center justify-between p-2 rounded hover:bg-muted/50 cursor-pointer"
                onClick={() => router.push(`/cus/bookings/${apt.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {apt.service?.name || 'Service'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(apt.start_time).toLocaleDateString('en-GB', {
                      weekday: 'short',
                      day: 'numeric',
                      month: 'short',
                    })} at {formatTime(apt.start_time)}
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs ml-2 ${
                  apt.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                  apt.status === 'in_progress' ? 'bg-green-100 text-green-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {apt.status}
                </span>
              </div>
            ))}
          </div>
          {appointments.length > 5 && (
            <Link href="/cus/bookings" className="block text-center text-sm text-primary hover:underline mt-2">
              View all {appointments.length} appointments →
            </Link>
          )}
        </div>
      )}

      {appointments.length === 0 && (
        <div className="text-center py-6 text-sm text-muted-foreground">
          No upcoming appointments
          <div className="mt-2">
            <Link href="/booking" className="text-primary hover:underline">
              Book a service →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
