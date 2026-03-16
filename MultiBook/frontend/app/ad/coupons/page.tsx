'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export interface CouponListEntry {
  id: number
  code: string
  name: string
  discount_type: 'percentage' | 'fixed'
  discount_value: string
  max_uses: number | null
  used_count: number
  valid_from: string
  valid_until: string | null
  minimum_order_amount: string
  status: string
  is_valid: boolean
}

interface CouponListResponse {
  success: boolean
  data?: CouponListEntry[]
  meta?: { count?: number }
}

/**
 * Admin Coupons List Page
 * Route: /ad/coupons (Security: /ad/)
 */
export default function AdminCouponsList() {
  const router = useRouter()
  const [coupons, setCoupons] = useState<CouponListEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    fetchCoupons()
  }, [statusFilter])

  const fetchCoupons = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = new URLSearchParams()
      if (statusFilter !== 'all') params.append('status', statusFilter)
      const url = `${ADMIN_ENDPOINTS.COUPONS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<CouponListResponse>(url)
      if (response.data.success && response.data.data) {
        setCoupons(response.data.data)
      } else {
        setError('Failed to load coupons')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load coupons')
      console.error('Error fetching coupons:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this coupon? This cannot be undone.')) return
    try {
      await apiClient.delete(ADMIN_ENDPOINTS.COUPONS.DELETE(id))
      fetchCoupons()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete coupon')
      console.error('Error deleting coupon:', err)
    }
  }

  const formatDate = (d: string | null) => {
    if (!d) return '—'
    return new Date(d).toLocaleDateString('en-GB', { dateStyle: 'short' })
  }

  const discountLabel = (c: CouponListEntry) => {
    if (c.discount_type === 'percentage') return `${c.discount_value}% off`
    return `£${parseFloat(c.discount_value).toFixed(2)} off`
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Coupons</h1>
              <p className="text-muted-foreground">
                Create and manage discount codes for bookings
              </p>
            </div>
            <Button onClick={() => router.push('/ad/coupons/new')}>
              Create Coupon
            </Button>
          </div>

          <div className="mb-6 flex gap-2">
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('all')}
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'active' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('active')}
            >
              Active
            </Button>
            <Button
              variant={statusFilter === 'inactive' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('inactive')}
            >
              Inactive
            </Button>
            <Button
              variant={statusFilter === 'expired' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('expired')}
            >
              Expired
            </Button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading coupons...</p>
            </div>
          )}

          {!loading && !error && (
            <div className="space-y-4">
              {coupons.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground border rounded-lg">
                  <p className="text-lg mb-2">No coupons found</p>
                  <Button onClick={() => router.push('/ad/coupons/new')} variant="outline">
                    Create your first coupon
                  </Button>
                </div>
              ) : (
                <div className="border rounded-lg overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Code</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Discount</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Used</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Valid from</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Valid until</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {coupons.map((c) => (
                        <tr key={c.id} className="hover:bg-muted/50">
                          <td className="px-4 py-3 font-mono font-medium">{c.code}</td>
                          <td className="px-4 py-3">{c.name}</td>
                          <td className="px-4 py-3">{discountLabel(c)}</td>
                          <td className="px-4 py-3">{c.used_count}{c.max_uses != null ? ` / ${c.max_uses}` : ''}</td>
                          <td className="px-4 py-3">{formatDate(c.valid_from)}</td>
                          <td className="px-4 py-3">{formatDate(c.valid_until)}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded ${
                              c.status === 'active' ? 'bg-green-100 text-green-800' :
                              c.status === 'expired' ? 'bg-gray-100 text-gray-600' : 'bg-muted text-muted-foreground'
                            }`}>
                              {c.status}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2">
                              <Button variant="outline" size="sm" asChild>
                                <Link href={`/ad/coupons/${c.id}`}>Edit</Link>
                              </Button>
                              <Button variant="destructive" size="sm" onClick={() => handleDelete(c.id)}>
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
