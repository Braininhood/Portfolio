'use client'

import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { StaffSchedule, StaffScheduleResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'

export function TodaySchedule() {
  const [schedule, setSchedule] = useState<StaffSchedule[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSchedule()
  }, [])

  const fetchSchedule = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<StaffScheduleResponse>(STAFF_ENDPOINTS.SCHEDULE)
      if (response.data.success && response.data.data) {
        setSchedule(response.data.data.filter(s => s.is_active))
      }
    } catch (err: any) {
      console.error('Error fetching schedule:', err)
    } finally {
      setLoading(false)
    }
  }

  const today = new Date().getDay()
  // Convert Sunday (0) to 6, Monday (1) to 0, etc.
  const dayOfWeek = today === 0 ? 6 : today - 1
  
  const todaySchedule = schedule.find(s => s.day_of_week === dayOfWeek)

  if (loading) {
    return <div className="text-center py-4 text-muted-foreground">Loading schedule...</div>
  }

  if (!todaySchedule) {
    return (
      <div className="bg-card border rounded-lg p-6 text-center text-muted-foreground">
        No schedule for today
      </div>
    )
  }

  return (
    <div className="bg-card border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">
          {todaySchedule.day_name || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dayOfWeek]}
        </h3>
        <div className="text-sm text-muted-foreground">
          {todaySchedule.start_time} - {todaySchedule.end_time}
        </div>
      </div>
      
      {todaySchedule.breaks && todaySchedule.breaks.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="text-sm font-medium mb-2">Breaks:</div>
          <div className="space-y-1">
            {todaySchedule.breaks.map((breakPeriod, idx) => (
              <div key={idx} className="text-sm text-muted-foreground">
                {breakPeriod.start} - {breakPeriod.end}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
