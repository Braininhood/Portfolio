'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import Link from 'next/link'

interface Subscription {
  id: number
  subscription_number: string
  customer_name: string
  service_name: string
  frequency: string
  duration_months: number
  start_date: string
  end_date: string
  status: string
  total_appointments: number
  completed_appointments: number
  total_price: string
  payment_status: string
  is_guest_subscription?: boolean
}

interface SubscriptionListResponse {
  success?: boolean
  data?: Subscription[]
  results?: Subscription[]
  count?: number
}

/**
 * Customer Subscriptions Page
 * Route: /cus/subscriptions (Security: /cus/)
 */
export default function CustomerSubscriptions() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [actionLoading, setActionLoading] = useState<number | null>(null)

  useEffect(() => {
    fetchSubscriptions()
  }, [statusFilter])

  const fetchSubscriptions = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }

      const response = await apiClient.get<SubscriptionListResponse>(
        `${CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      )

      const raw = response.data as SubscriptionListResponse
      const list = raw.data ?? raw.results ?? []
      setSubscriptions(Array.isArray(list) ? list : [])
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : null
      setError(message || 'Failed to load subscriptions')
      console.error('Error fetching subscriptions:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async (id: number) => {
    try {
      setActionLoading(id)
      await apiClient.post(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.PAUSE(id))
      await fetchSubscriptions()
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : null
      setError(message || 'Failed to pause subscription')
    } finally {
      setActionLoading(null)
    }
  }

  const handleActivate = async (id: number) => {
    try {
      setActionLoading(id)
      await apiClient.post(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.ACTIVATE(id))
      await fetchSubscriptions()
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : null
      setError(message || 'Failed to activate subscription')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancel = async (id: number) => {
    if (!confirm('Are you sure you want to cancel this subscription? This cannot be undone.')) return
    try {
      setActionLoading(id)
      await apiClient.post(CUSTOMER_ENDPOINTS.SUBSCRIPTIONS.CANCEL(id))
      await fetchSubscriptions()
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : null
      setError(message || 'Failed to cancel subscription')
    } finally {
      setActionLoading(null)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  const formatCurrency = (amount: string | number) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
    }).format(num)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'paused':
        return 'bg-amber-100 text-amber-800'
      case 'cancelled':
        return 'bg-red-100 text-red-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const frequencyLabel = (freq: string) => {
    switch (freq) {
      case 'weekly': return 'Weekly'
      case 'biweekly': return 'Bi-weekly'
      case 'monthly': return 'Monthly'
      default: return freq
    }
  }

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">My Subscriptions</h1>
            <p className="text-muted-foreground">
              View and manage your recurring cleaning subscriptions
            </p>
          </div>

          {/* Status Filter */}
          <div className="mb-6">
            <div className="flex gap-2 flex-wrap">
              {(['all', 'active', 'paused', 'cancelled', 'completed'] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-4 py-2 rounded-md text-sm font-medium min-h-[44px] ${
                    statusFilter === status
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading subscriptions...</p>
            </div>
          )}

          {/* Subscriptions List */}
          {!loading && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {subscriptions.length} subscription{subscriptions.length !== 1 ? 's' : ''}
              </div>
              {subscriptions.length === 0 ? (
                <div className="bg-card border rounded-lg p-12 text-center text-muted-foreground">
                  No subscriptions found
                  <div className="mt-4">
                    <Link href="/booking" className="text-primary hover:underline">
                      Book a subscription →
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {subscriptions.map((sub) => (
                    <div
                      key={sub.id}
                      className="bg-card border rounded-lg p-6 hover:shadow-md transition-shadow"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                        <div>
                          <div className="font-mono font-semibold text-lg">{sub.subscription_number}</div>
                          <div className="text-lg font-medium mt-1">{sub.service_name}</div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {frequencyLabel(sub.frequency)} · {sub.duration_months} month{sub.duration_months !== 1 ? 's' : ''} · {formatDate(sub.start_date)} – {formatDate(sub.end_date)}
                          </div>
                          <div className="flex items-center gap-2 mt-2">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(sub.status)}`}>
                              {sub.status}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {sub.completed_appointments} / {sub.total_appointments} visits
                            </span>
                            <span className="text-sm text-muted-foreground">
                              · {formatCurrency(sub.total_price)}
                            </span>
                            {sub.payment_status && (
                              <span className="text-xs text-muted-foreground capitalize">
                                ({sub.payment_status})
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2 shrink-0">
                          {sub.status === 'active' && (
                            <button
                              onClick={() => handlePause(sub.id)}
                              disabled={actionLoading === sub.id}
                              className="px-4 py-2 rounded-md text-sm font-medium bg-amber-100 text-amber-800 hover:bg-amber-200 disabled:opacity-50"
                            >
                              {actionLoading === sub.id ? 'Pausing…' : 'Pause'}
                            </button>
                          )}
                          {sub.status === 'paused' && (
                            <button
                              onClick={() => handleActivate(sub.id)}
                              disabled={actionLoading === sub.id}
                              className="px-4 py-2 rounded-md text-sm font-medium bg-green-100 text-green-800 hover:bg-green-200 disabled:opacity-50"
                            >
                              {actionLoading === sub.id ? 'Activating…' : 'Activate'}
                            </button>
                          )}
                          {(sub.status === 'active' || sub.status === 'paused') && (
                            <button
                              onClick={() => handleCancel(sub.id)}
                              disabled={actionLoading === sub.id}
                              className="px-4 py-2 rounded-md text-sm font-medium bg-destructive/10 text-destructive hover:bg-destructive/20 disabled:opacity-50"
                            >
                              {actionLoading === sub.id ? 'Cancelling…' : 'Cancel subscription'}
                            </button>
                          )}
                          <Link
                            href={`/cus/subscriptions/${sub.id}`}
                            className="px-4 py-2 rounded-md text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20"
                          >
                            Manage visits
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
