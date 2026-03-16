'use client'

/**
 * Customer Calendar Sync Widget – uses shared CalendarSyncWidget.
 * Kept for backwards compatibility; prefer importing from @/components/calendar/CalendarSyncWidget.
 */
import { CalendarSyncWidget } from '@/components/calendar/CalendarSyncWidget'

export function CustomerCalendarSyncWidget() {
  return (
    <CalendarSyncWidget
      settingsHref="/cus/calendar/settings"
      subtitle="Sync your appointments with your calendar"
    />
  )
}
