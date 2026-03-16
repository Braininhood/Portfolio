'use client'

/**
 * Staff Service Areas Management
 * Route: /st/areas
 * List/create/edit/delete postcode + radius; optional per-service area.
 */
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { STAFF_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'

interface StaffAreaItem {
  id: number
  postcode: string
  radius_miles: number
  service?: number | null
  service_id?: number | null
  service_name?: string | null
  is_active: boolean
  created_at?: string
  updated_at?: string
}

interface StaffServiceOption {
  id: number
  name: string
}

export default function StaffAreasPage() {
  const [areas, setAreas] = useState<StaffAreaItem[]>([])
  const [services, setServices] = useState<StaffServiceOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    postcode: '',
    radius_miles: 5,
    service_id: null as number | null,
  })
  const [submitLoading, setSubmitLoading] = useState(false)

  useEffect(() => {
    fetchAreas()
    fetchServicesForDropdown()
  }, [])

  const fetchAreas = async () => {
    try {
      setError(null)
      const res = await apiClient.get<{ success?: boolean; data?: StaffAreaItem[] } | StaffAreaItem[]>(STAFF_ENDPOINTS.AREAS.LIST)
      const data = res.data
      if (data && typeof data === 'object' && 'data' in data && Array.isArray(data.data)) {
        setAreas(data.data)
      } else if (Array.isArray(data)) {
        setAreas(data)
      } else {
        setError('Failed to load areas')
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } }; status?: number } }
      if (ax.response?.status === 401) setError('Please log in again.')
      else setError(ax.response?.data?.error?.message || 'Failed to load areas')
    } finally {
      setLoading(false)
    }
  }

  const fetchServicesForDropdown = async () => {
    try {
      const res = await apiClient.get<{ success: boolean; data: StaffAreaItem[] }>(STAFF_ENDPOINTS.SERVICES.LIST)
      if (res.data?.success && Array.isArray(res.data.data)) {
        setServices((res.data.data as unknown as { id: number; name: string }[]).map((s) => ({ id: s.id, name: s.name })))
      }
    } catch {
      // Optional for dropdown
    }
  }

  const openCreate = () => {
    setEditingId(null)
    setFormData({ postcode: '', radius_miles: 5, service_id: null })
    setShowForm(true)
  }

  const openEdit = (a: StaffAreaItem) => {
    setEditingId(a.id)
    setFormData({
      postcode: a.postcode,
      radius_miles: a.radius_miles,
      service_id: a.service ?? a.service_id ?? null,
    })
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const postcode = formData.postcode.trim().toUpperCase().replace(/\s+/g, ' ')
    if (!postcode) {
      setError('Please enter a postcode')
      return
    }
    setSubmitLoading(true)
    setError(null)
    try {
      const payload: { postcode: string; radius_miles: number; service_id?: number | null } = {
        postcode,
        radius_miles: Number(formData.radius_miles),
      }
      if (formData.service_id != null && formData.service_id > 0) {
        payload.service_id = formData.service_id
      }
      if (editingId) {
        await apiClient.patch(STAFF_ENDPOINTS.AREAS.UPDATE(editingId), payload)
      } else {
        await apiClient.post(STAFF_ENDPOINTS.AREAS.CREATE, payload)
      }
      setShowForm(false)
      setEditingId(null)
      fetchAreas()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string }; detail?: unknown } } }
      const msg = ax.response?.data?.error?.message ?? (typeof ax.response?.data?.detail === 'string' ? ax.response.data.detail : 'Failed to save')
      setError(msg)
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this area?')) return
    try {
      await apiClient.delete(STAFF_ENDPOINTS.AREAS.DELETE(id))
      fetchAreas()
      setShowForm(false)
      setEditingId(null)
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: { message?: string } } } }
      setError(ax.response?.data?.error?.message || 'Failed to delete')
    }
  }

  return (
    <ProtectedRoute requiredRole={['staff']}>
      <DashboardLayout>
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-2xl font-bold">My Service Areas</h1>
            <Button onClick={openCreate}>Add area</Button>
          </div>

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          {showForm && (
            <div className="p-6 border border-border rounded-lg bg-card">
              <h2 className="text-lg font-semibold mb-4">{editingId ? 'Edit area' : 'New area'}</h2>
              <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium mb-1">Postcode (UK)</label>
                  <input
                    type="text"
                    required
                    value={formData.postcode}
                    onChange={(e) => setFormData((f) => ({ ...f, postcode: e.target.value.toUpperCase().trim() }))}
                    placeholder="e.g. SW1A 1AA"
                    className="w-full px-3 py-2 border border-border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Radius (miles)</label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={formData.radius_miles}
                    onChange={(e) => setFormData((f) => ({ ...f, radius_miles: Number(e.target.value) }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Service (optional)</label>
                  <select
                    value={formData.service_id ?? ''}
                    onChange={(e) => setFormData((f) => ({ ...f, service_id: e.target.value ? Number(e.target.value) : null }))}
                    className="w-full px-3 py-2 border border-border rounded-md"
                  >
                    <option value="">All my services</option>
                    {services.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  <p className="text-xs text-muted-foreground mt-1">Leave as &quot;All my services&quot; to cover all services from this postcode.</p>
                </div>
                <div className="flex gap-2">
                  <Button type="submit" disabled={submitLoading}>
                    {submitLoading ? 'Saving...' : editingId ? 'Update' : 'Add area'}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingId(null) }}>
                    Cancel
                  </Button>
                </div>
              </form>
            </div>
          )}

          {loading ? (
            <p className="text-muted-foreground">Loading areas...</p>
          ) : areas.length === 0 ? (
            <div className="p-6 border border-border rounded-lg text-center text-muted-foreground">
              No service areas yet. Add a postcode and radius to define where you can provide services. Customers in that area will see you as available.
            </div>
          ) : (
            <div className="border border-border rounded-lg overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-3">Postcode</th>
                    <th className="text-left p-3">Radius (miles)</th>
                    <th className="text-left p-3">Service</th>
                    <th className="text-left p-3">Active</th>
                    <th className="text-right p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {areas.map((a) => (
                    <tr key={a.id} className="border-t border-border">
                      <td className="p-3 font-medium">{a.postcode}</td>
                      <td className="p-3">{a.radius_miles}</td>
                      <td className="p-3">{a.service_name ?? 'All my services'}</td>
                      <td className="p-3">{a.is_active ? 'Yes' : 'No'}</td>
                      <td className="p-3 text-right">
                        <Button variant="outline" size="sm" className="mr-1" onClick={() => openEdit(a)}>
                          Edit
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDelete(a.id)}>
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="text-sm text-muted-foreground">
            Areas define where you are available. Add a postcode and radius; optionally link an area to a specific service so it only applies to that service.
          </p>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
