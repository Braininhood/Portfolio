'use client'

/**
 * Shared calendar sync settings content.
 * Used by /settings/calendar (all roles) and /st/calendar/settings (staff).
 * settingsPath: used for OAuth return replaceState (e.g. /st/calendar/settings).
 * backHref/backLabel: optional Back link (else router.back()).
 */
import { Fragment, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import { useAuthContext } from '@/components/auth/AuthProvider'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { CALENDAR_ENDPOINTS, STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment } from '@/types/appointment'

interface CalendarStatus {
  calendar_sync_enabled: boolean
  calendar_provider: 'none' | 'google' | 'outlook' | 'apple'
  calendar_calendar_id: string | null
  has_access_token: boolean
  has_refresh_token: boolean
  last_sync_at: string | null
  last_sync_error: string | null
}

interface CalendarSettingsContentProps {
  settingsPath?: string
  backHref?: string
  backLabel?: string
}

export function CalendarSettingsContent({
  settingsPath,
  backHref,
  backLabel = 'Back',
}: CalendarSettingsContentProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { user } = useAuthContext()
  const [status, setStatus] = useState<CalendarStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [connecting, setConnecting] = useState<'google' | 'outlook' | null>(null)
  const [showAddEvent, setShowAddEvent] = useState(false)
  const [events, setEvents] = useState<Array<{ id: number; start: string; end: string; summary: string; synced_to: string[] }>>([])
  const [customEventForm, setCustomEventForm] = useState({
    title: '',
    start: '',
    end: '',
    description: '',
    location: '',
  })
  const [weekStart, setWeekStart] = useState(() => {
    const d = new Date()
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1)
    return new Date(d.getFullYear(), d.getMonth(), diff)
  })
  const [staffJobs, setStaffJobs] = useState<Appointment[]>([])

  const isAdmin = user?.role === 'admin'
  const isStaff = user?.role === 'staff'
  const replacePath = settingsPath ?? pathname ?? '/settings/calendar'

  useEffect(() => {
    fetchStatus()
    fetchEvents()
  }, [])

  useEffect(() => {
    if (!isStaff) {
      setStaffJobs([])
      return
    }
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)
    const dateFrom = weekStart.toISOString().slice(0, 10)
    const dateTo = weekEnd.toISOString().slice(0, 10)
    apiClient
      .get(STAFF_ENDPOINTS.JOBS.LIST, { params: { date_from: dateFrom, date_to: dateTo } })
      .then((res) => {
        const raw = res.data as { results?: Appointment[]; data?: Appointment[]; success?: boolean }
        const list = raw?.results ?? (raw?.success && raw?.data ? raw.data : null)
        setStaffJobs(Array.isArray(list) ? list : [])
      })
      .catch(() => setStaffJobs([]))
  }, [isStaff, weekStart])

  useEffect(() => {
    const connected = searchParams?.get('connected')
    const err = searchParams?.get('error')
    if (connected) {
      setMessage({ type: 'success', text: `Connected to ${connected === 'google' ? 'Google Calendar' : 'Microsoft Outlook'}.` })
      fetchStatus()
      if (typeof window !== 'undefined') window.history.replaceState({}, '', replacePath)
    }
    if (err) {
      let errorText = 'Connection failed.'
      if (err === 'google_oauth_error' || err === 'token_exchange_failed') {
        errorText = 'Google connection failed. Please check that the redirect URI matches Google Cloud Console settings.'
      } else if (err === 'redirect_uri_mismatch') {
        errorText = 'Redirect URI mismatch. Please verify the callback URL is configured correctly in Google Cloud Console.'
      } else if (err === 'invalid_grant') {
        errorText = 'Authorization code expired or invalid. Please try connecting again.'
      } else if (err === 'invalid_client') {
        errorText = 'Invalid OAuth credentials. Please check server configuration.'
      } else if (err === 'outlook_oauth_error') {
        errorText = 'Outlook connection failed.'
      }
      setMessage({ type: 'error', text: errorText })
      if (typeof window !== 'undefined') window.history.replaceState({}, '', replacePath)
    }
  }, [searchParams, replacePath])

  const fetchStatus = async () => {
    try {
      setLoading(true)
      setMessage(null)
      const res = await apiClient.get(CALENDAR_ENDPOINTS.STATUS)
      if (res.data.success && res.data.data) setStatus(res.data.data)
      else setStatus(null)
    } catch (e: any) {
      const code = e.response?.data?.error?.code
      const msg = e.response?.data?.error?.message || e.message
      if (e.response?.status === 404 || code === 'PROFILE_NOT_FOUND') {
        setStatus({
          calendar_sync_enabled: false,
          calendar_provider: 'none',
          calendar_calendar_id: null,
          has_access_token: false,
          has_refresh_token: false,
          last_sync_at: null,
          last_sync_error: null,
        })
        setMessage({ type: 'error', text: 'Your profile could not be loaded. Please refresh the page or contact support.' })
      } else {
        setMessage({ type: 'error', text: msg || 'Failed to load calendar status' })
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchEvents = async () => {
    try {
      const res = await apiClient.get(CALENDAR_ENDPOINTS.EVENTS)
      if (res.data.success && res.data.data?.events) setEvents(res.data.data.events)
    } catch {
      setEvents([])
    }
  }

  const handleConnect = async (provider: 'google' | 'outlook') => {
    try {
      setConnecting(provider)
      setMessage(null)
      const endpoint = provider === 'google' ? CALENDAR_ENDPOINTS.GOOGLE_CONNECT : CALENDAR_ENDPOINTS.OUTLOOK_CONNECT
      const res = await apiClient.post(endpoint)
      const url = res.data?.data?.authorization_url || res.data?.authorization_url
      if (url) window.location.href = url
      else setMessage({ type: 'error', text: 'Could not get authorization URL' })
    } catch (e: any) {
      const code = e.response?.data?.error?.code
      const statusCode = e.response?.status
      if (statusCode === 503 || code === 'MISSING_CONFIG' || code === 'LIBRARY_NOT_INSTALLED') {
        setMessage({
          type: 'error',
          text: `${provider === 'google' ? 'Google' : 'Outlook'} sync is temporarily unavailable (not configured on the server). Use Apple Calendar instead: add appointments via the .ics download link on individual appointment or job pages.`,
        })
      } else {
        setMessage({ type: 'error', text: e.response?.data?.error?.message || `Failed to start ${provider} connection` })
      }
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async () => {
    if (!status?.calendar_provider || status.calendar_provider === 'none') return
    if (!confirm('Disconnect this calendar?')) return
    try {
      const endpoint = status.calendar_provider === 'google' ? CALENDAR_ENDPOINTS.GOOGLE_DISCONNECT : CALENDAR_ENDPOINTS.OUTLOOK_DISCONNECT
      await apiClient.post(endpoint)
      setMessage({ type: 'success', text: 'Calendar disconnected.' })
      fetchStatus()
      setEvents([])
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.error?.message || 'Failed to disconnect' })
    }
  }

  const handleSync = async () => {
    try {
      setSyncing(true)
      setMessage(null)
      const res = await apiClient.post(CALENDAR_ENDPOINTS.SYNC)
      if (res.data.success) {
        const data = res.data.data
        setMessage({ type: 'success', text: data?.message || `Synced ${data?.synced_count ?? 0} appointment(s).` })
        fetchStatus()
        fetchEvents()
      } else {
        setMessage({ type: 'error', text: res.data?.error?.message || 'Sync failed' })
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.response?.data?.error?.message || 'Sync failed. Try again.' })
    } finally {
      setSyncing(false)
    }
  }

  const handleAddCustomEvent = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!customEventForm.title.trim() || !customEventForm.start || !customEventForm.end) {
      setMessage({ type: 'error', text: 'Title, start and end are required.' })
      return
    }
    try {
      const startISO = new Date(customEventForm.start).toISOString()
      const endISO = new Date(customEventForm.end).toISOString()
      await apiClient.post(CALENDAR_ENDPOINTS.EVENTS, {
        title: customEventForm.title,
        start: startISO,
        end: endISO,
        description: customEventForm.description,
        location: customEventForm.location,
      })
      setMessage({ type: 'success', text: 'Event added to your calendar.' })
      setShowAddEvent(false)
      setCustomEventForm({ title: '', start: '', end: '', description: '', location: '' })
      fetchEvents()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error?.message || 'Failed to create event' })
    }
  }

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
    } catch {
      return iso
    }
  }

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(weekStart.getDate() + i)
    return d
  })
  const hours = Array.from({ length: 16 }, (_, i) => i + 8)
  const now = new Date()
  const todayStr = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`
  const currentHour = now.getHours()
  const currentDayIndex = weekDays.findIndex(
    (d) => d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  )
  const eventsByDayHour: Record<string, typeof events> = {}
  events.forEach((ev) => {
    const d = new Date(ev.start)
    const dayIdx = weekDays.findIndex(
      (w) => w.getFullYear() === d.getFullYear() && w.getMonth() === d.getMonth() && w.getDate() === d.getDate()
    )
    if (dayIdx < 0) return
    const hour = d.getHours()
    const key = `${dayIdx}-${hour}`
    if (!eventsByDayHour[key]) eventsByDayHour[key] = []
    eventsByDayHour[key].push(ev)
  })
  const jobsByDayHour: Record<string, Appointment[]> = {}
  staffJobs.forEach((job) => {
    const d = new Date(job.start_time)
    const dayIdx = weekDays.findIndex(
      (w) => w.getFullYear() === d.getFullYear() && w.getMonth() === d.getMonth() && w.getDate() === d.getDate()
    )
    if (dayIdx < 0) return
    const hour = d.getHours()
    const key = `${dayIdx}-${hour}`
    if (!jobsByDayHour[key]) jobsByDayHour[key] = []
    jobsByDayHour[key].push(job)
  })

  return (
    <div className="container mx-auto p-4 md:p-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">Calendar sync</h1>
            <p className="text-muted-foreground">
              Connect Google Calendar, Outlook, or Apple Calendar
            </p>
          </div>
          {backHref ? (
            <Link href={backHref}>
              <Button variant="outline">{backLabel}</Button>
            </Link>
          ) : (
            <Button variant="outline" onClick={() => router.back()}>
              {backLabel}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        <div className="lg:col-span-2 order-2 lg:order-1">
          <div className="rounded-lg border bg-card p-3 sticky top-4">
            <div className="flex items-center justify-between mb-2">
              <button
                type="button"
                onClick={() => {
                  const prev = new Date(weekStart)
                  prev.setDate(prev.getDate() - 7)
                  setWeekStart(prev)
                }}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                ←
              </button>
              <span className="text-xs font-medium">
                {weekDays[0].toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} – {weekDays[6].toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
              </span>
              <button
                type="button"
                onClick={() => {
                  const next = new Date(weekStart)
                  next.setDate(next.getDate() + 7)
                  setWeekStart(next)
                }}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                →
              </button>
            </div>
            <div className="text-[10px] text-muted-foreground mb-1">
              {typeof Intl !== 'undefined' && Intl.DateTimeFormat().resolvedOptions().timeZone?.replace(/^.*\//, '') || 'Local'}
            </div>
            <div className="overflow-x-auto rounded border border-border">
              <div className="grid gap-0 min-w-0" style={{ gridTemplateColumns: '28px repeat(7, 1fr)' }}>
              <div className="bg-muted/50" />
              {weekDays.map((d, col) => {
                const isToday = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}` === todayStr
                return (
                  <div
                    key={col}
                    className={`text-center py-0.5 text-[10px] font-medium ${isToday ? 'bg-primary/20 text-primary' : 'text-muted-foreground'}`}
                  >
                    {['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'][col]}
                    <div className={`text-[11px] mt-0.5 ${isToday ? 'font-bold' : ''}`}>{d.getDate()}</div>
                  </div>
                )
              })}
              {hours.map((hour) => (
                <Fragment key={hour}>
                  <div className="bg-muted/30 text-[10px] text-muted-foreground py-0.5 pr-1 text-right border-t border-border">
                    {hour.toString().padStart(2, '0')}:00
                  </div>
                  {weekDays.map((d, col) => {
                    const isToday = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}` === todayStr
                    const key = `${col}-${hour}`
                    const cellEvents = eventsByDayHour[key] || []
                    const cellJobs = jobsByDayHour[key] || []
                    const isCurrentTime = currentDayIndex === col && currentHour === hour
                    return (
                      <div
                        key={`${hour}-${col}`}
                        className={`min-h-[14px] border-t border-border text-[9px] ${isToday ? 'bg-primary/5' : ''} ${isCurrentTime ? 'relative' : ''}`}
                      >
                        {isCurrentTime && (
                          <div className="absolute left-0 right-0 top-0 h-0.5 bg-red-500 z-10 flex items-center">
                            <div className="w-1 h-1 rounded-full bg-red-500" />
                          </div>
                        )}
                        {cellJobs.length > 0 && (
                          <div className="flex flex-col gap-0.5">
                            {cellJobs.map((job) => (
                              <Link
                                key={job.id}
                                href={`/st/jobs/${job.id}`}
                                className="text-primary truncate block hover:underline"
                                title={job.service?.name || `Job #${job.id}`}
                              >
                                {job.service?.name || `#${job.id}`}
                              </Link>
                            ))}
                          </div>
                        )}
                        {cellEvents.length > 0 && cellJobs.length === 0 && (
                          <span className="text-primary truncate block" title={cellEvents.map((e) => e.summary).join(', ')}>
                            {cellEvents.length}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </Fragment>
              ))}
            </div>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2">
              {isStaff ? 'Your jobs are shown; click to open. ' : ''}
              Synced events in grid. Red line = now.
            </p>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6 order-1 lg:order-2">
          {message && (
            <div
              className={`rounded-lg border p-4 ${
                message.type === 'success' ? 'border-green-200 bg-green-50 text-green-800' : 'border-destructive/50 bg-destructive/10 text-destructive'
              }`}
            >
              {message.text}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
            </div>
          ) : (
            <>
              <section className="rounded-lg border bg-card p-6">
                <h2 className="text-lg font-semibold mb-4">Connection</h2>
                {status?.calendar_sync_enabled && status.calendar_provider !== 'none' ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">
                          {status.calendar_provider === 'google' && 'Google Calendar'}
                          {status.calendar_provider === 'outlook' && 'Microsoft Outlook'}
                          {status.calendar_provider === 'apple' && 'Apple Calendar'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {status.has_access_token && 'Access token • '}
                          {status.has_refresh_token && 'Refresh token'}
                        </p>
                      </div>
                      <Button variant="outline" size="sm" onClick={handleDisconnect}>
                        Disconnect
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm">
                      {status.last_sync_at && (
                        <span className="text-muted-foreground">
                          Last sync: {formatDate(status.last_sync_at)}
                        </span>
                      )}
                      {status.last_sync_error && (
                        <span className="text-destructive">Error: {status.last_sync_error}</span>
                      )}
                    </div>
                    <Button onClick={handleSync} disabled={syncing}>
                      {syncing ? 'Syncing…' : 'Sync now'}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-muted-foreground">Connect a calendar to sync appointments.</p>
                    <div className="flex flex-wrap gap-3">
                      <Button onClick={() => handleConnect('google')} disabled={!!connecting}>
                        {connecting === 'google' ? 'Redirecting…' : 'Connect Google Calendar'}
                      </Button>
                      <Button variant="outline" onClick={() => handleConnect('outlook')} disabled={!!connecting}>
                        {connecting === 'outlook' ? 'Redirecting…' : 'Connect Outlook'}
                      </Button>
                    </div>
                    <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                      <p className="text-sm font-medium text-blue-900">Apple Calendar (always available)</p>
                      <p className="text-sm text-blue-800 mt-1">
                        If Google or Outlook sync is unavailable, you can add appointments to Apple Calendar using the <strong>.ics download link</strong> on individual appointment or job pages.
                      </p>
                    </div>
                  </div>
                )}
              </section>

              <section className="rounded-lg border border-muted bg-muted/30 p-4">
                <h3 className="text-sm font-semibold mb-2">Apple Calendar</h3>
                <p className="text-sm text-muted-foreground">
                  Use the .ics download link on individual appointments to add them to Apple Calendar. No server configuration required.
                </p>
              </section>

              {status?.calendar_sync_enabled && status.calendar_provider !== 'none' && (
                <section className="rounded-lg border bg-card p-6">
                  <h2 className="text-lg font-semibold mb-4">Custom event</h2>
                  {!showAddEvent ? (
                    <Button variant="outline" onClick={() => setShowAddEvent(true)}>
                      Add event to calendar
                    </Button>
                  ) : (
                    <form onSubmit={handleAddCustomEvent} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Title</label>
                        <input
                          className="w-full rounded-md border px-3 py-2"
                          value={customEventForm.title}
                          onChange={(e) => setCustomEventForm((p) => ({ ...p, title: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">Start (datetime-local)</label>
                          <input
                            type="datetime-local"
                            className="w-full rounded-md border px-3 py-2"
                            value={customEventForm.start}
                            onChange={(e) => setCustomEventForm((p) => ({ ...p, start: e.target.value }))}
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">End</label>
                          <input
                            type="datetime-local"
                            className="w-full rounded-md border px-3 py-2"
                            value={customEventForm.end}
                            onChange={(e) => setCustomEventForm((p) => ({ ...p, end: e.target.value }))}
                            required
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Description (optional)</label>
                        <textarea
                          className="w-full rounded-md border px-3 py-2"
                          rows={2}
                          value={customEventForm.description}
                          onChange={(e) => setCustomEventForm((p) => ({ ...p, description: e.target.value }))}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Location (optional)</label>
                        <input
                          className="w-full rounded-md border px-3 py-2"
                          value={customEventForm.location}
                          onChange={(e) => setCustomEventForm((p) => ({ ...p, location: e.target.value }))}
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button type="submit">Create event</Button>
                        <Button type="button" variant="outline" onClick={() => setShowAddEvent(false)}>
                          Cancel
                        </Button>
                      </div>
                    </form>
                  )}
                </section>
              )}

              {status?.calendar_sync_enabled && events.length > 0 && (
                <section className="rounded-lg border bg-card p-6">
                  <h2 className="text-lg font-semibold mb-4">Synced appointments</h2>
                  <ul className="space-y-2">
                    {events.slice(0, 20).map((ev) => (
                      <li key={ev.id} className="flex justify-between text-sm border-b pb-2">
                        <span>{ev.summary}</span>
                        <span className="text-muted-foreground">{formatDate(ev.start)}</span>
                      </li>
                    ))}
                  </ul>
                  {events.length > 20 && <p className="text-sm text-muted-foreground mt-2">Showing first 20</p>}
                </section>
              )}

              {isAdmin && (
                <section className="rounded-lg border bg-card p-6">
                  <h2 className="text-lg font-semibold mb-2">Admin</h2>
                  <p className="text-sm text-muted-foreground mb-2">Bulk sync calendars for staff or customers.</p>
                  <Button variant="outline" onClick={() => router.push('/ad/settings/calendar')}>
                    Open bulk sync
                  </Button>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
