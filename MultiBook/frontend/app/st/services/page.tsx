'use client'

/**
 * Staff Services Management
 * Route: /st/services
 * List (assigned + created), create (pending approval), edit/delete own pending only.
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import type { Category, CategoryListResponse } from '@/types/service'
import { useEffect, useState } from 'react'
interface StaffServiceItem {
  id: number
  name: string
  slug: string
  description?: string | null
  duration: number
  price: string | number
  currency: string
  category_name?: string
  is_active: boolean
  approval_status: 'approved' | 'pending_approval'
  created_by_me: boolean
  my_price_override?: number | null
  my_duration_override?: number | null
  extras?: unknown[]
}

export default function StaffServicesPage() {
  const [services, setServices] = useState<StaffServiceItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingOverridesId, setEditingOverridesId] = useState<number | null>(null)
  const [overridesForm, setOverridesForm] = useState({ duration: 60 })
  const [formData, setFormData] = useState({
    category_id: 0,
    name: '',
    description: '',
    duration: 60,
    price: '0',
    currency: 'GBP',
  })
  const [submitLoading, setSubmitLoading] = useState(false)

  useEffect(() => {
    fetchServices()
    fetchCategories()
  }, [])

  const fetchServices = async () => {
    try {
      setError(null)
      const res = await apiClient.get<{ success: boolean; data: StaffServiceItem[] }>(STAFF_ENDPOINTS.SERVICES.LIST)
      if (res.data?.success && Array.isArray(res.data.data)) {
        setServices(res.data.data)
      } else {
        setError('Failed to load services')
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } }; status?: number } }
      if (ax.response?.status === 401) setError('Please log in again.')
      else setError(ax.response?.data?.error?.message || 'Failed to load services')
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const res = await apiClient.get<CategoryListResponse>(STAFF_ENDPOINTS.CATEGORIES.LIST)
      if (res.data?.success && Array.isArray(res.data.data)) {
        setCategories(res.data.data)
      }
    } catch {
      // Categories optional for list; needed for create
    }
  }

  const openCreate = () => {
    setEditingId(null)
    setFormData({
      category_id: categories[0]?.id ?? 0,
      name: '',
      description: '',
      duration: 60,
      price: '0',
      currency: 'GBP',
    })
    setShowForm(true)
  }

  const openEdit = (s: StaffServiceItem) => {
    if (s.created_by_me && s.approval_status === 'pending_approval') {
      setEditingOverridesId(null)
      setEditingId(s.id)
      setFormData({
        category_id: 0,
        name: s.name,
        description: s.description || '',
        duration: s.my_duration_override ?? s.duration,
        price: String(s.my_price_override ?? s.price),
        currency: s.currency || 'GBP',
      })
      setShowForm(true)
    } else {
      setEditingId(null)
      setShowForm(false)
      setEditingOverridesId(s.id)
      setOverridesForm({
        duration: s.my_duration_override ?? s.duration,
      })
    }
  }

  const handleSubmitOverrides = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingOverridesId) return
    setSubmitLoading(true)
    try {
      await apiClient.patch(STAFF_ENDPOINTS.SERVICES.UPDATE(editingOverridesId), {
        my_duration_override: Number(overridesForm.duration),
      })
      setEditingOverridesId(null)
      fetchServices()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } }
      setError(ax.response?.data?.error?.message || 'Failed to update')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitLoading(true)
    try {
      if (editingId) {
        await apiClient.patch(STAFF_ENDPOINTS.SERVICES.UPDATE(editingId), {
          name: formData.name,
          description: formData.description || undefined,
          duration: Number(formData.duration),
          price: Number(formData.price),
          currency: formData.currency,
        })
      } else {
        await apiClient.post(STAFF_ENDPOINTS.SERVICES.CREATE, {
          category_id: formData.category_id,
          name: formData.name,
          description: formData.description || undefined,
          duration: Number(formData.duration),
          price: Number(formData.price),
          currency: formData.currency,
        })
      }
      setShowForm(false)
      setEditingId(null)
      fetchServices()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } }
      setError(ax.response?.data?.error?.message || 'Failed to save')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleRemove = async (s: StaffServiceItem) => {
    const isOwnPending = s.created_by_me && s.approval_status === 'pending_approval'
    const msg = isOwnPending
      ? 'Delete this service? It will be removed permanently and will no longer be available for anyone.'
      : 'Remove this service from your list? You will no longer offer it; the service stays available for other staff.'
    if (!confirm(msg)) return
    try {
      await apiClient.delete(STAFF_ENDPOINTS.SERVICES.DELETE(s.id))
      fetchServices()
      setShowForm(false)
      setEditingId(null)
      setEditingOverridesId(null)
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } }
      setError(ax.response?.data?.error?.message || 'Failed to remove')
    }
  }

  return (
    <ProtectedRoute requiredRole={['staff']}>
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-2xl font-bold">My Services</h1>
            <Button onClick={openCreate} disabled={categories.length === 0}>
              Add service
            </Button>
          </div>

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          {showForm && (
            <div className="p-6 border border-border rounded-lg bg-card">
              <h2 className="text-lg font-semibold mb-4">{editingId ? 'Edit service' : 'New service (pending approval)'}</h2>
              <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
                {!editingId && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Category</label>
                    <select
                      required
                      value={formData.category_id}
                      onChange={(e) => setFormData((f) => ({ ...f, category_id: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-border rounded-md"
                    >
                      <option value={0}>Select category</option>
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-1">Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData((f) => ({ ...f, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description (optional)</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData((f) => ({ ...f, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                    rows={2}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Duration (minutes)</label>
                    <input
                      type="number"
                      min={1}
                      value={formData.duration}
                      onChange={(e) => setFormData((f) => ({ ...f, duration: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-border rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Price</label>
                    <input
                      type="number"
                      min={0}
                      step={0.01}
                      value={formData.price}
                      onChange={(e) => setFormData((f) => ({ ...f, price: e.target.value }))}
                      className="w-full px-3 py-2 border border-border rounded-md"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button type="submit" disabled={submitLoading}>
                    {submitLoading ? 'Saving...' : editingId ? 'Update' : 'Create (pending approval)'}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingId(null) }}>
                    Cancel
                  </Button>
                </div>
              </form>
            </div>
          )}

          {loading ? (
            <p className="text-muted-foreground">Loading services...</p>
          ) : services.length === 0 ? (
            <div className="p-6 border border-border rounded-lg text-center text-muted-foreground">
              No services yet. Add a service (it will need admin approval before customers can book it) or ask a manager to assign you to existing services.
            </div>
          ) : (
            <div className="border border-border rounded-lg overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-3">Service</th>
                    <th className="text-left p-3">Category</th>
                    <th className="text-left p-3">Duration</th>
                    <th className="text-left p-3">Price</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-right p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {services.map((s) => (
                    <tr key={s.id} className="border-t border-border">
                      <td className="p-3 font-medium">{s.name}</td>
                      <td className="p-3">{s.category_name ?? '—'}</td>
                      <td className="p-3">{s.my_duration_override ?? s.duration} min</td>
                      <td className="p-3">
                        £{typeof s.price === 'string' ? parseFloat(s.price).toFixed(2) : (s.my_price_override ?? s.price).toFixed(2)}
                      </td>
                      <td className="p-3">
                        {s.approval_status === 'pending_approval' ? (
                          <span className="text-amber-600">Pending approval</span>
                        ) : (
                          <span className="text-green-600">Approved</span>
                        )}
                        {s.created_by_me && (
                          <span className="ml-1 text-muted-foreground">(you created)</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {editingOverridesId === s.id ? (
                          <form onSubmit={handleSubmitOverrides} className="inline-flex flex-wrap items-center gap-2">
                            <label className="text-sm text-muted-foreground">Duration (min):</label>
                            <input
                              type="number"
                              min={1}
                              value={overridesForm.duration}
                              onChange={(e) => setOverridesForm((f) => ({ ...f, duration: Number(e.target.value) }))}
                              className="w-16 px-2 py-1 border border-border rounded text-sm"
                            />
                            <Button type="submit" size="sm" disabled={submitLoading}>Save</Button>
                            <Button type="button" variant="outline" size="sm" onClick={() => setEditingOverridesId(null)}>Cancel</Button>
                          </form>
                        ) : (
                          <>
                            <Button variant="outline" size="sm" className="mr-1" onClick={() => openEdit(s)}>
                              {s.created_by_me && s.approval_status === 'pending_approval' ? 'Edit' : 'Edit my duration'}
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => handleRemove(s)}>
                              {s.created_by_me && s.approval_status === 'pending_approval' ? 'Delete' : 'Remove from my services'}
                            </Button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="text-sm text-muted-foreground">
            Services you create are sent for approval. You can remove any service from your list (it will no longer appear for you). Services you created while still pending can be fully edited or deleted; approved or assigned services can only have your duration changed or be removed from your list (price is set by the service).
          </p>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
