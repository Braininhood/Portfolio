'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { CALENDAR_ENDPOINTS, STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Appointment, AppointmentDetailResponse } from '@/types/appointment'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

/**
 * Staff Job Detail Page
 * Route: /st/jobs/[id] (Security: /st/)
 */
export default function StaffJobDetail() {
  const router = useRouter()
  const params = useParams()
  const jobId = params.id as string

  const [job, setJob] = useState<Appointment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    fetchJob()
  }, [jobId])

  const fetchJob = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<AppointmentDetailResponse>(
        STAFF_ENDPOINTS.JOBS.DETAIL(jobId)
      )
      const jobData =
        response.data?.success && response.data?.data
          ? response.data.data
          : null
      if (jobData && typeof jobData === 'object' && 'id' in jobData) {
        setJob(jobData)
        setNotes(jobData.internal_notes || '')
      } else {
        setError('Failed to load job')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load job')
      console.error('Error fetching job:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCheckIn = async () => {
    try {
      setActionLoading(true)
      setError(null)
      
      await apiClient.post(STAFF_ENDPOINTS.JOBS.CHECKIN(jobId))
      fetchJob() // Refresh job data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to check in')
      console.error('Error checking in:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleComplete = async () => {
    try {
      setActionLoading(true)
      setError(null)
      
      await apiClient.post(STAFF_ENDPOINTS.JOBS.COMPLETE(jobId), {
        notes: notes || undefined,
      })
      fetchJob() // Refresh job data
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to complete job')
      console.error('Error completing job:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const _handleUpdateStatus = async (newStatus: string) => {
    try {
      setActionLoading(true)
      setError(null)
      
      // TODO: Add status update endpoint if needed
      // For now, we'll use check-in/complete actions
      if (newStatus === 'in_progress') {
        await handleCheckIn()
      } else if (newStatus === 'completed') {
        await handleComplete()
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to update status')
      console.error('Error updating status:', err)
    } finally {
      setActionLoading(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('en-GB', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      }),
      time: date.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    }
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minutes`
    }
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours} hour${hours !== 1 ? 's' : ''} ${mins} minute${mins !== 1 ? 's' : ''}` : `${hours} hour${hours !== 1 ? 's' : ''}`
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="staff">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading job details...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (!job) {
    return (
      <ProtectedRoute requiredRole="staff">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
              Job not found
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const { date, time } = formatDateTime(job.start_time)
  // Staff can only see confirmed appointments, so check-in/complete only for confirmed/in_progress
  const canCheckIn = job.status === 'confirmed'
  const canComplete = job.status === 'in_progress' || job.status === 'confirmed'

  // Add to calendar (only when job is defined)
  const toGoogleDate = (iso: string) => {
    const d = new Date(iso)
    const y = d.getUTCFullYear()
    const m = String(d.getUTCMonth() + 1).padStart(2, '0')
    const day = String(d.getUTCDate()).padStart(2, '0')
    const h = String(d.getUTCHours()).padStart(2, '0')
    const min = String(d.getUTCMinutes()).padStart(2, '0')
    const s = String(d.getUTCSeconds()).padStart(2, '0')
    return `${y}${m}${day}T${h}${min}${s}Z`
  }
  const calendarTitle = encodeURIComponent(job.service?.name || `MultiBook Job #${job.id}`)
  const calendarStart = toGoogleDate(job.start_time)
  const calendarEnd = toGoogleDate(job.end_time)
  const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${calendarTitle}&dates=${calendarStart}/${calendarEnd}`
  const outlookCalendarUrl = `https://outlook.live.com/calendar/0/action/compose?subject=${calendarTitle}&startdt=${encodeURIComponent(job.start_time)}&enddt=${encodeURIComponent(job.end_time)}`

  const handleDownloadIcs = async () => {
    try {
      const res = await apiClient.get(CALENDAR_ENDPOINTS.ICS(job.id), { responseType: 'blob' })
      const blob = res.data as Blob
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `multibook-job-${job.id}.ics`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to download calendar file')
    }
  }

  return (
    <ProtectedRoute requiredRole="staff">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-8">
            <Button variant="outline" onClick={() => router.push('/st/jobs')} className="mb-4">
              ← Back to Jobs
            </Button>
            <h1 className="text-3xl font-bold mb-2">{job.service?.name || 'Job Details'}</h1>
            <p className="text-muted-foreground">
              {date} at {time}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Job Information */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Job Information</h2>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Service</div>
                    <div className="font-medium">{job.service?.name}</div>
                    {job.service && (
                      <div className="text-sm text-muted-foreground mt-1">
                        Duration: {formatDuration(job.service.duration)}
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Date & Time</div>
                    <div className="font-medium">{date}</div>
                    <div className="text-sm text-muted-foreground">{time}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-muted-foreground">Status</div>
                    <span className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                      job.status === 'completed' ? 'bg-green-100 text-green-800' :
                      job.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                      job.status === 'confirmed' ? 'bg-yellow-100 text-yellow-800' :
                      job.status === 'pending' ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                  
                  {job.appointment_type && (
                    <div>
                      <div className="text-sm text-muted-foreground">Type</div>
                      <div className="font-medium">
                        {job.appointment_type === 'subscription' && '📅 Subscription'}
                        {job.appointment_type === 'order_item' && '📦 Order Item'}
                        {job.appointment_type === 'single' && '📋 Single Appointment'}
                      </div>
                      {job.subscription_number && (
                        <div className="text-sm text-muted-foreground mt-1">
                          Subscription: {job.subscription_number}
                        </div>
                      )}
                      {job.order_number && (
                        <div className="text-sm text-muted-foreground mt-1">
                          Order: {job.order_number}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Customer Information */}
              {job.customer_booking?.customer && (
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
                  <div className="space-y-2">
                    <div>
                      <div className="text-sm text-muted-foreground">Name</div>
                      <div className="font-medium">{job.customer_booking.customer.name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Email</div>
                      <div>{job.customer_booking.customer.email}</div>
                    </div>
                    {job.customer_booking.customer.phone && (
                      <div>
                        <div className="text-sm text-muted-foreground">Phone</div>
                        <div>{job.customer_booking.customer.phone}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Location Notes */}
              {job.location_notes && (
                <div className="bg-card border rounded-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Location Notes</h2>
                  <p className="text-muted-foreground whitespace-pre-wrap">{job.location_notes}</p>
                </div>
              )}

              {/* Internal Notes */}
              <div className="bg-card border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Internal Notes</h2>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={4}
                  placeholder="Add notes about this job..."
                />
                <Button
                  onClick={async () => {
                    try {
                      await apiClient.patch(STAFF_ENDPOINTS.JOBS.DETAIL(jobId), {
                        internal_notes: notes,
                      })
                      fetchJob()
                    } catch (err: any) {
                      setError(err.response?.data?.error?.message || 'Failed to save notes')
                    }
                  }}
                  className="mt-2"
                  variant="outline"
                >
                  Save Notes
                </Button>
              </div>

            </div>

            {/* Actions Sidebar */}
            <div className="space-y-6">
              <div className="bg-card border rounded-lg p-6 sticky top-4">
                <h2 className="text-xl font-semibold mb-4">Actions</h2>
                <div className="space-y-3">
                  {canCheckIn && (
                    <Button
                      onClick={handleCheckIn}
                      disabled={actionLoading}
                      className="w-full"
                    >
                      {actionLoading ? 'Processing...' : 'Check In'}
                    </Button>
                  )}
                  
                  {canComplete && (
                    <Button
                      onClick={handleComplete}
                      disabled={actionLoading}
                      variant={job.status === 'in_progress' ? 'default' : 'outline'}
                      className="w-full"
                    >
                      {actionLoading ? 'Processing...' : 'Complete Job'}
                    </Button>
                  )}
                  
                  {job.status === 'completed' && (
                    <div className="text-center text-green-600 font-medium">
                      ✓ Job Completed
                    </div>
                  )}
                </div>
              </div>

              {/* Add to calendar */}
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Add to calendar</h3>
                <div className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full justify-start" onClick={handleDownloadIcs}>
                    Apple Calendar (.ics)
                  </Button>
                  <a href={googleCalendarUrl} target="_blank" rel="noopener noreferrer" className="block">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      Google Calendar
                    </Button>
                  </a>
                  <a href={outlookCalendarUrl} target="_blank" rel="noopener noreferrer" className="block">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      Outlook
                    </Button>
                  </a>
                </div>
              </div>

              {/* Quick Info */}
              <div className="bg-card border rounded-lg p-6">
                <h3 className="font-semibold mb-3">Quick Info</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Service:</span>
                    <span className="ml-2">{job.service?.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="ml-2">{job.service ? formatDuration(job.service.duration) : '-'}</span>
                  </div>
                  {job.customer_booking && (
                    <div>
                      <span className="text-muted-foreground">Price:</span>
                      <span className="ml-2">£{parseFloat(job.customer_booking.total_price.toString()).toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
