'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Service, ServiceListResponse } from '@/types/service'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'

export interface CouponDetail {
  id: number
  code: string
  name: string
  discount_type: 'percentage' | 'fixed'
  discount_value: string
  max_uses: number | null
  max_uses_per_customer: number | null
  used_count: number
  valid_from: string
  valid_until: string | null
  minimum_order_amount: string
  applicable_services: { id: number; name: string }[]
  excluded_services: { id: number; name: string }[]
  applicable_service_ids?: number[]
  excluded_service_ids?: number[]
  status: string
  description: string | null
}

interface CouponDetailResponse {
  success: boolean
  data?: CouponDetail
}

const toDatetimeLocal = (iso: string | null): string => {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/**
 * Admin Coupon Create/Edit Page
 * Route: /ad/coupons/new | /ad/coupons/[id]
 */
export default function AdminCouponDetail() {
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const isNew = id === 'new'

  const [coupon, setCoupon] = useState<CouponDetail | null>(null)
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    discount_type: 'percentage' as 'percentage' | 'fixed',
    discount_value: '',
    max_uses: '',
    max_uses_per_customer: '1',
    valid_from: '',
    valid_until: '',
    minimum_order_amount: '0',
    applicable_service_ids: [] as number[],
    excluded_service_ids: [] as number[],
    status: 'active',
    description: '',
  })

  useEffect(() => {
    fetchServices()
    if (isNew) {
      setLoading(false)
      const now = new Date()
      const pad = (n: number) => n.toString().padStart(2, '0')
      setFormData(prev => ({
        ...prev,
        valid_from: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T00:00`,
      }))
    } else {
      fetchCoupon()
    }
  }, [id])

  const fetchServices = async () => {
    try {
      const response = await apiClient.get<ServiceListResponse>(ADMIN_ENDPOINTS.SERVICES.LIST)
      if (response.data.success && response.data.data) {
        setServices(response.data.data)
      }
    } catch (err) {
      console.error('Error fetching services:', err)
    }
  }

  const fetchCoupon = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get<CouponDetailResponse>(ADMIN_ENDPOINTS.COUPONS.DETAIL(parseInt(id)))
      if (response.data.success && response.data.data) {
        const d = response.data.data
        setCoupon(d)
        const fromIds = (d.applicable_services || []).map((s: { id: number }) => s.id)
        const exclIds = (d.excluded_services || []).map((s: { id: number }) => s.id)
        setFormData({
          code: d.code,
          name: d.name,
          discount_type: d.discount_type,
          discount_value: d.discount_value,
          max_uses: d.max_uses != null ? String(d.max_uses) : '',
          max_uses_per_customer: d.max_uses_per_customer != null ? String(d.max_uses_per_customer) : '1',
          valid_from: toDatetimeLocal(d.valid_from),
          valid_until: toDatetimeLocal(d.valid_until),
          minimum_order_amount: d.minimum_order_amount || '0',
          applicable_service_ids: fromIds,
          excluded_service_ids: exclIds,
          status: d.status,
          description: d.description || '',
        })
      } else {
        setError('Failed to load coupon')
      }
    } catch (err: any) {
      if (err.response?.status === 404) setError('Coupon not found')
      else setError(err.response?.data?.error?.message || 'Failed to load coupon')
      console.error('Error fetching coupon:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!formData.code.trim() || !formData.name.trim()) {
      setError('Code and name are required')
      return
    }
    if (!formData.valid_from) {
      setError('Valid from date is required')
      return
    }
    const val = parseFloat(formData.discount_value)
    if (isNaN(val) || val < 0) {
      setError('Discount value must be a non-negative number')
      return
    }
    if (formData.discount_type === 'percentage' && val > 100) {
      setError('Percentage discount cannot exceed 100')
      return
    }

    try {
      setSaving(true)
      const payload = {
        code: formData.code.trim().toUpperCase(),
        name: formData.name.trim(),
        discount_type: formData.discount_type,
        discount_value: formData.discount_value,
        max_uses: formData.max_uses ? parseInt(formData.max_uses, 10) : null,
        max_uses_per_customer: formData.max_uses_per_customer ? parseInt(formData.max_uses_per_customer, 10) : null,
        valid_from: new Date(formData.valid_from).toISOString(),
        valid_until: formData.valid_until ? new Date(formData.valid_until).toISOString() : null,
        minimum_order_amount: formData.minimum_order_amount || '0',
        applicable_service_ids: formData.applicable_service_ids,
        excluded_service_ids: formData.excluded_service_ids,
        status: formData.status,
        description: formData.description.trim() || null,
      }

      if (isNew) {
        const response = await apiClient.post(ADMIN_ENDPOINTS.COUPONS.CREATE, payload)
        if (response.data.success && response.data.data?.id) {
          router.push(`/ad/coupons/${response.data.data.id}`)
        } else {
          setError('Failed to create coupon')
        }
      } else {
        const response = await apiClient.patch(ADMIN_ENDPOINTS.COUPONS.UPDATE(parseInt(id)), payload)
        if (response.data.success) {
          setCoupon(response.data.data)
          setError(null)
        } else {
          setError('Failed to update coupon')
        }
      }
    } catch (err: any) {
      const msg = err.response?.data?.error?.message
        || (err.response?.data && typeof err.response.data === 'object' && Object.values(err.response.data).flat().join(', '))
        || 'Failed to save coupon'
      setError(msg)
      console.error('Error saving coupon:', err)
    } finally {
      setSaving(false)
    }
  }

  const toggleService = (serviceId: number, field: 'applicable_service_ids' | 'excluded_service_ids') => {
    setFormData(prev => {
      const arr = prev[field]
      const next = arr.includes(serviceId) ? arr.filter(i => i !== serviceId) : [...arr, serviceId]
      return { ...prev, [field]: next }
    })
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12 text-muted-foreground">Loading coupon...</div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {isNew ? 'Create Coupon' : (coupon?.name || coupon?.code || 'Coupon')}
              </h1>
              <p className="text-muted-foreground">
                {isNew ? 'Add a new discount code' : 'Edit coupon details'}
              </p>
            </div>
            {!isNew && (
              <Button variant="outline" asChild>
                <Link href="/ad/coupons">Back to list</Link>
              </Button>
            )}
          </div>

          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-6 max-w-2xl">
            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-lg font-semibold">Basic info</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Code *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value.toUpperCase() }))}
                    className="w-full px-3 py-2 border rounded-md font-mono"
                    placeholder="SAVE20"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="20% off"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description (optional)</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={2}
                />
              </div>
            </div>

            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-lg font-semibold">Discount</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Type</label>
                  <select
                    value={formData.discount_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, discount_type: e.target.value as 'percentage' | 'fixed' }))}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="percentage">Percentage</option>
                    <option value="fixed">Fixed amount (£)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Value *</label>
                  <input
                    type="number"
                    min="0"
                    max={formData.discount_type === 'percentage' ? 100 : undefined}
                    step={formData.discount_type === 'percentage' ? 1 : 0.01}
                    value={formData.discount_value}
                    onChange={(e) => setFormData(prev => ({ ...prev, discount_value: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder={formData.discount_type === 'percentage' ? '20' : '5.00'}
                    required
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    {formData.discount_type === 'percentage' ? '0–100' : 'Amount in GBP'}
                  </p>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Minimum order amount (£)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.minimum_order_amount}
                  onChange={(e) => setFormData(prev => ({ ...prev, minimum_order_amount: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>

            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-lg font-semibold">Validity</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Valid from *</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_from}
                    onChange={(e) => setFormData(prev => ({ ...prev, valid_from: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Valid until (optional)</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_until}
                    onChange={(e) => setFormData(prev => ({ ...prev, valid_until: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Max total uses (optional)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_uses}
                    onChange={(e) => setFormData(prev => ({ ...prev, max_uses: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="Unlimited"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max uses per customer (optional)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.max_uses_per_customer}
                    onChange={(e) => setFormData(prev => ({ ...prev, max_uses_per_customer: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>
              {!isNew && (
                <div>
                  <label className="block text-sm font-medium mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="expired">Expired</option>
                  </select>
                </div>
              )}
            </div>

            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-lg font-semibold">Service restrictions (optional)</h2>
              <p className="text-sm text-muted-foreground">
                By default a coupon applies to all services. Restrict to specific services or exclude some below.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Applies only to these services (leave empty = all)</label>
                  <div className="max-h-40 overflow-y-auto border rounded p-2 space-y-1">
                    {services.map((s) => (
                      <label key={s.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.applicable_service_ids.includes(s.id!)}
                          onChange={() => toggleService(s.id!, 'applicable_service_ids')}
                        />
                        <span className="text-sm">{s.name}</span>
                      </label>
                    ))}
                    {services.length === 0 && <span className="text-muted-foreground text-sm">No services</span>}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Excluded services</label>
                  <div className="max-h-40 overflow-y-auto border rounded p-2 space-y-1">
                    {services.map((s) => (
                      <label key={s.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.excluded_service_ids.includes(s.id!)}
                          onChange={() => toggleService(s.id!, 'excluded_service_ids')}
                        />
                        <span className="text-sm">{s.name}</span>
                      </label>
                    ))}
                    {services.length === 0 && <span className="text-muted-foreground text-sm">No services</span>}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving...' : isNew ? 'Create coupon' : 'Save changes'}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/ad/coupons">Cancel</Link>
              </Button>
            </div>
          </form>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
