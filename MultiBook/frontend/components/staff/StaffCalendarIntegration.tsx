'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS, CALENDAR_ENDPOINTS } from '@/lib/api/endpoints'

interface StaffCalendarIntegrationProps {
  staffId: number
  staffUserId?: number | null
}

interface CalendarStatus {
  calendar_sync_enabled: boolean
  calendar_provider: 'none' | 'google' | 'outlook' | 'apple'
  calendar_calendar_id: string | null
  has_access_token: boolean
  has_refresh_token: boolean
}

interface Appointment {
  id: number
  service: {
    name: string
  }
  start_time: string
  end_time: string
  status: string
}

export function StaffCalendarIntegration({ staffId, staffUserId }: StaffCalendarIntegrationProps) {
  const [status, setStatus] = useState<CalendarStatus | null>(null)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingAppointments, setLoadingAppointments] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [_connecting, setConnecting] = useState(false)

  useEffect(() => {
    if (staffUserId) {
      fetchStatus()
    } else {
      setLoading(false)
    }
    fetchAppointments()
  }, [staffUserId, staffId])

  const fetchStatus = async () => {
    if (!staffUserId) return

    try {
      setLoading(true)
      setError(null)
      
      // Get calendar status for the staff member's user account
      const response = await apiClient.get(
        `${ADMIN_ENDPOINTS.CALENDAR.STATUS}?user_id=${staffUserId}`
      )
      
      if (response.data.success && response.data.data) {
        setStatus(response.data.data)
      }
    } catch (err: any) {
      // If user doesn't have calendar connected, that's okay
      if (err.response?.status !== 404) {
        setError(err.response?.data?.error?.message || 'Failed to load calendar status')
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchAppointments = async () => {
    try {
      setLoadingAppointments(true)
      // Get upcoming appointments for this staff member
      const today = new Date().toISOString().split('T')[0]
      const response = await apiClient.get(
        `${ADMIN_ENDPOINTS.APPOINTMENTS.LIST}?staff_id=${staffId}&date_from=${today}`
      )
      
      if (response.data.success && response.data.data) {
        setAppointments(response.data.data)
      }
    } catch (err: any) {
      console.error('Error fetching appointments:', err)
    } finally {
      setLoadingAppointments(false)
    }
  }

  const handleDownloadICS = async (appointmentId: number) => {
    try {
      // Download ICS file
      const response = await apiClient.get(
        CALENDAR_ENDPOINTS.ICS(appointmentId),
        { responseType: 'blob' }
      )
      
      // Create blob and download
      const blob = new Blob([response.data], { type: 'text/calendar' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `appointment-${appointmentId}.ics`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to download ICS file')
      console.error('Error downloading ICS:', err)
    }
  }

  const handleDownloadAllICS = async () => {
    if (appointments.length === 0) {
      alert('No appointments to download')
      return
    }

    try {
      // Download ICS files one by one (or create a combined file)
      for (const appointment of appointments) {
        await handleDownloadICS(appointment.id)
        // Small delay between downloads
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    } catch (err: any) {
      alert('Failed to download some ICS files')
      console.error('Error downloading ICS files:', err)
    }
  }

  const _handleConnect = async (_provider: 'google' | 'outlook') => {
    try {
      setConnecting(true)
      setError(null)

      // Note: Calendar connection must be done by the staff member themselves
      // Admin can view status but cannot connect on behalf of staff
      // Redirect to staff login or show message
      alert('Calendar connection must be done by the staff member from their own account. Please ask the staff member to log in and connect their calendar.')
      setConnecting(false)
      return

      // The code below would work if we had staff impersonation or admin-level connection
      // For now, staff members need to connect their own calendars
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to connect calendar')
      console.error('Error connecting calendar:', err)
    } finally {
      setConnecting(false)
    }
  }

  const _handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect the calendar?')) {
      return
    }

    try {
      const provider = status?.calendar_provider || 'google'
      const endpoint = provider === 'google'
        ? CALENDAR_ENDPOINTS.GOOGLE_DISCONNECT
        : CALENDAR_ENDPOINTS.OUTLOOK_DISCONNECT

      await apiClient.post(endpoint)
      fetchStatus() // Refresh status
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to disconnect calendar')
      console.error('Error disconnecting calendar:', err)
    }
  }

  // Appointments list + ICS downloads (admin can always see this for any staff)
  const appointmentsSection = (
    <div className="border rounded-lg p-6 space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="font-semibold">Upcoming appointments</h4>
          <p className="text-sm text-muted-foreground">
            View and download .ics for Apple Calendar (or import into other calendars)
          </p>
        </div>
        {appointments.length > 0 && (
          <Button onClick={handleDownloadAllICS} variant="outline" size="sm">
            Download All ({appointments.length})
          </Button>
        )}
      </div>
      {loadingAppointments ? (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto" />
          <p className="mt-2 text-xs text-muted-foreground">Loading appointments...</p>
        </div>
      ) : appointments.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">
          No upcoming appointments found for this staff member.
        </p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {appointments.map((appointment) => (
            <div
              key={appointment.id}
              className="flex items-center justify-between border rounded-lg p-3 hover:bg-muted/50"
            >
              <div className="flex-1">
                <div className="font-medium text-sm">{appointment.service.name}</div>
                <div className="text-xs text-muted-foreground">
                  {new Date(appointment.start_time).toLocaleString('en-GB', {
                    weekday: 'short',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                  {' • '}
                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                    appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                    appointment.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                    appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {appointment.status}
                  </span>
                </div>
              </div>
              <Button onClick={() => handleDownloadICS(appointment.id)} variant="outline" size="sm">
                Download .ics
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  if (!staffUserId) {
    return (
      <div className="space-y-4">
        <div className="border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Calendar sync</h3>
          <p className="text-muted-foreground">
            Google/Outlook/Apple calendar sync is tied to a <strong>user account</strong>. This staff record has no linked user yet.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Link a user account in the <strong>Basic Info</strong> tab so the staff can log in and connect their calendar. You can still view their appointments and download .ics below.
          </p>
        </div>
        {appointmentsSection}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-2 text-sm text-muted-foreground">Loading calendar status...</p>
      </div>
    )
  }

  const isConnected = status?.calendar_sync_enabled && status.calendar_provider !== 'none'

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Calendar Integration</h3>
          <p className="text-sm text-muted-foreground">
            Sync appointments with Google Calendar, Outlook, or Apple Calendar
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 text-destructive text-sm rounded">
          {error}
        </div>
      )}

      {/* Connection Status */}
      {isConnected ? (
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">
                Connected to {status.calendar_provider === 'google' ? 'Google Calendar' : 
                             status.calendar_provider === 'outlook' ? 'Microsoft Outlook' : 
                             'Apple Calendar'}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                Calendar sync is active
                {status.calendar_calendar_id && (
                  <span className="ml-2">• Calendar ID: {status.calendar_calendar_id.substring(0, 20)}...</span>
                )}
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              Staff member must disconnect from their own account
            </div>
          </div>

          <div className="flex gap-2 text-sm">
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${status.has_access_token ? 'bg-green-500' : 'bg-gray-400'}`}></div>
              <span>Access Token</span>
            </div>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${status.has_refresh_token ? 'bg-green-500' : 'bg-gray-400'}`}></div>
              <span>Refresh Token</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-6 space-y-4">
          <p className="text-muted-foreground">
            No calendar connected. Connect a calendar to automatically sync appointments.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>Note:</strong> Calendar connection must be done by the staff member from their own account.
            </p>
            <p className="text-xs text-blue-700 mt-2">
              The staff member needs to log in to their account and connect their calendar in the settings.
              Admin can view the connection status here.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 opacity-60">
            <div className="border rounded-lg p-4 flex flex-col items-center gap-2">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              <span className="text-sm">Google Calendar</span>
            </div>

            <div className="border rounded-lg p-4 flex flex-col items-center gap-2">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.5 7.5h9v9h-9z" fill="#0078D4"/>
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="#0078D4"/>
              </svg>
              <span className="text-sm">Microsoft Outlook</span>
            </div>

            <div className="border rounded-lg p-4 flex flex-col items-center gap-2">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
              </svg>
              <span className="text-sm">Apple Calendar</span>
              <span className="text-xs">(.ics download)</span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground text-center">
            Apple Calendar uses .ics file downloads (no API sync available)
          </p>
        </div>
      )}

      {appointmentsSection}
    </div>
  )
}
