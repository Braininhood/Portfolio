'use client'

/**
 * Staff Calendar Sync Widget – uses shared CalendarSyncWidget.
 * Kept for backwards compatibility; prefer importing from @/components/calendar/CalendarSyncWidget.
 */
import { CalendarSyncWidget as SharedCalendarSyncWidget } from '@/components/calendar/CalendarSyncWidget'

export function CalendarSyncWidget() {
  return (
    <SharedCalendarSyncWidget
      settingsHref="/st/calendar/settings"
      subtitle="Sync your jobs with your calendar"
    />
  )
}
