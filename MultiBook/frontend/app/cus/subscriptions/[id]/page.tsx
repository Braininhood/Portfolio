'use client'

/**
 * Customer Subscription Detail – manage each visit (like order).
 * Route: /cus/subscriptions/[id]
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface SubAppointment {
  id: number
  sequence_number: number
  scheduled_date: string
  status: string
  can_cancel: boolean
  can_reschedule?: boolean
  cancellation_deadline: string | null
  appointment?: { start_time?: string; end_time?: string; service?: { name?: string } }
}

interface SubscriptionDetail {
  id: number
  subscription_number: string
  status: string
  frequency: string
  duration_months: number
  start_date: string
  end_date: string
  total_appointments: number
  completed_appointments: number
  total_price: string
  service_name?: string
  service?: { name?: string }
  appointments?: SubAppointment[]
}

export default function SubscriptionDetailPage() {
  const _router = useRouter()
  const params = useParams()
  const id = params?.id as string
  const [sub, setSub] = useState<SubscriptionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [changeRequestVisitId, setChangeRequestVisitId] = useState<number | null>(null)
  const [changeRequestDate, setChangeRequestDate] = useState('')
  const [changeRequestTime, setChangeRequestTime] = useState('')
  const [changeRequestReason, setChangeRequestReason] = useState('')
  const [changeRequestSubmitting, setChangeRequestSubmitting] = useState(false)
  const [changeRequestError, setChangeRequestError] = useState<string | null>(null)

  useEffect(() => {
    if (id) fetchSubscription()
  }, [id])

  const fetchSubscription = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.DETAIL(parseInt(id)))
      const raw = response.data as { success?: boolean; data?: SubscriptionDetail }
      const data = raw?.data ?? response.data
      if (data && (data.subscription_number || (data as SubscriptionDetail).id)) {
        setSub(data as SubscriptionDetail)
      } else {
        setError('Subscription not found')
      }
    } catch (err: any) {
      setError(err.response?.status === 404 ? 'Subscription not found' : (err.response?.data?.error?.message || 'Failed to load subscription'))
    } finally {
      setLoading(false)
    }
  }

  const handleCancelVisit = async (subApptId: number) => {
    if (!confirm('Cancel this visit? This cannot be undone.')) return
    try {
      setActionLoading(subApptId)
      await apiClient.post(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.APPOINTMENT_CANCEL(parseInt(id), subApptId))
      await fetchSubscription()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to cancel visit')
    } finally {
      setActionLoading(null)
    }
  }

  const openRequestChange = (visit: SubAppointment) => {
    setChangeRequestVisitId(visit.id)
    setChangeRequestDate(visit.scheduled_date || '')
    const t = visit.appointment?.start_time
    if (t) {
      if (t.includes('T')) {
        const d = new Date(t)
        setChangeRequestTime(`${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`)
      } else {
        setChangeRequestTime(t.slice(0, 5))
      }
    } else {
      setChangeRequestTime('')
    }
    setChangeRequestReason('')
    setChangeRequestError(null)
  }

  const handleSubmitChangeRequest = async () => {
    if (!changeRequestVisitId || !changeRequestDate) {
      setChangeRequestError('Please select a new date.')
      return
    }
    try {
      setChangeRequestSubmitting(true)
      setChangeRequestError(null)
      await apiClient.post(
        CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.APPOINTMENT_REQUEST_CHANGE(parseInt(id), changeRequestVisitId),
        {
          scheduled_date: changeRequestDate,
          scheduled_time: changeRequestTime || undefined,
          reason: changeRequestReason || undefined,
        }
      )
      setChangeRequestVisitId(null)
      await fetchSubscription()
    } catch (err: any) {
      setChangeRequestError(err.response?.data?.error?.message || 'Failed to submit change request')
    } finally {
      setChangeRequestSubmitting(false)
    }
  }

  const formatDate = (d: string) => new Date(d).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
  const formatTime = (t: string | undefined) => {
    if (!t) return ''
    if (t.includes('T')) return new Date(t).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    return t.slice(0, 5)
  }
  const formatCurrency = (amount: string | number) =>
    new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(typeof amount === 'string' ? parseFloat(amount) : amount)
  const frequencyLabel = (f: string) => (f === 'weekly' ? 'Every week' : f === 'biweekly' ? 'Every 2 weeks' : f === 'monthly' ? 'Every month' : f)

  if (loading) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <p className="text-muted-foreground">Loading subscription...</p>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (error || !sub) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-4">{error || 'Subscription not found'}</div>
            <Button variant="outline" asChild><Link href="/cus/subscriptions">Back to Subscriptions</Link></Button>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const visits = sub.appointments ?? []

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <Button variant="outline" asChild className="mb-6">
            <Link href="/cus/subscriptions">← Back to Subscriptions</Link>
          </Button>

          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">{sub.subscription_number}</h1>
            <p className="text-muted-foreground">
              {sub.service_name || sub.service?.name} · {frequencyLabel(sub.frequency)} · {sub.duration_months} month{sub.duration_months !== 1 ? 's' : ''}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {sub.completed_appointments} / {sub.total_appointments} visits · {formatCurrency(sub.total_price)} · Status: {sub.status}
            </p>
          </div>

          <div className="mb-6 p-4 bg-muted/50 rounded-lg text-sm">
            <strong>24-hour policy:</strong> You can cancel or change a visit at least 24 hours before its scheduled time. After the deadline, that visit can no longer be changed or cancelled.
          </div>

          <h2 className="text-xl font-semibold mb-4">Your visits (manage each like an order)</h2>
          {visits.length === 0 ? (
            <div className="bg-card border rounded-lg p-8 text-center text-muted-foreground">
              No visits listed yet. They may be generated when the subscription is confirmed.
            </div>
          ) : (
            <div className="space-y-4">
              {visits.map((visit) => {
                const timeStr = visit.appointment?.start_time ? formatTime(visit.appointment.start_time) : ''
                const canCancel = visit.can_cancel && visit.status !== 'cancelled' && sub.status !== 'cancelled'
                const canReschedule = (visit.can_reschedule ?? visit.can_cancel) && visit.status !== 'cancelled' && sub.status !== 'cancelled'
                const showChangeForm = changeRequestVisitId === visit.id
                return (
                  <div
                    key={visit.id}
                    className="bg-card border rounded-lg p-6 flex flex-col gap-4"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div>
                        <div className="font-medium">
                          Visit #{visit.sequence_number} · {formatDate(visit.scheduled_date)}
                          {timeStr && ` at ${timeStr}`}
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            visit.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                            visit.status === 'completed' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {visit.status}
                          </span>
                          {visit.cancellation_deadline && visit.status !== 'cancelled' && (
                            <span className="text-xs text-muted-foreground">
                              Change/cancel by: {formatDate(visit.cancellation_deadline)} {visit.appointment?.start_time && formatTime(visit.appointment.start_time)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {canReschedule && !showChangeForm && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openRequestChange(visit)}
                          >
                            Request change
                          </Button>
                        )}
                        {canCancel && (
                          <Button
                            variant="destructive"
                            size="sm"
                            disabled={actionLoading === visit.id}
                            onClick={() => handleCancelVisit(visit.id)}
                          >
                            {actionLoading === visit.id ? 'Cancelling…' : 'Cancel this visit'}
                          </Button>
                        )}
                        {visit.status === 'cancelled' && (
                          <span className="text-sm text-muted-foreground">This visit was cancelled</span>
                        )}
                        {!visit.can_cancel && visit.status !== 'cancelled' && (
                          <span className="text-sm text-amber-700">Past 24h deadline</span>
                        )}
                      </div>
                    </div>
                    {showChangeForm && (
                      <div className="border-t pt-4 space-y-3">
                        <p className="text-sm font-medium">Request new date/time</p>
                        {changeRequestError && (
                          <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">{changeRequestError}</div>
                        )}
                        <div className="flex flex-wrap gap-3 items-end">
                          <div>
                            <label className="block text-xs text-muted-foreground mb-1">New date</label>
                            <input
                              type="date"
                              value={changeRequestDate}
                              onChange={(e) => setChangeRequestDate(e.target.value)}
                              className="border rounded px-2 py-1.5 text-sm"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-muted-foreground mb-1">New time (optional)</label>
                            <input
                              type="time"
                              value={changeRequestTime}
                              onChange={(e) => setChangeRequestTime(e.target.value)}
                              className="border rounded px-2 py-1.5 text-sm"
                            />
                          </div>
                          <div className="flex-1 min-w-[200px]">
                            <label className="block text-xs text-muted-foreground mb-1">Reason (optional)</label>
                            <input
                              type="text"
                              value={changeRequestReason}
                              onChange={(e) => setChangeRequestReason(e.target.value)}
                              placeholder="e.g. conflict with another appointment"
                              className="border rounded px-2 py-1.5 text-sm w-full"
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              disabled={changeRequestSubmitting}
                              onClick={handleSubmitChangeRequest}
                            >
                              {changeRequestSubmitting ? 'Submitting…' : 'Submit request'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={changeRequestSubmitting}
                              onClick={() => { setChangeRequestVisitId(null); setChangeRequestError(null) }}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
