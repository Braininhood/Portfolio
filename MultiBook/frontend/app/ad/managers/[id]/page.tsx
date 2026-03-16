'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

interface Manager {
  id: number
  user: {
    id: number
    email: string
    first_name?: string
    last_name?: string
    username?: string
  }
  permissions?: Record<string, any>
  can_manage_all: boolean
  can_manage_customers: boolean
  can_manage_staff: boolean
  can_manage_appointments: boolean
  can_view_reports: boolean
  managed_locations?: number[]
  managed_staff?: number[]
  managed_customers?: number[]
  is_active: boolean
  created_at?: string
  updated_at?: string
}

interface ManagerDetailResponse {
  success: boolean
  data: Manager
  meta: Record<string, never>
}

interface ManagerUpdateRequest {
  user_id?: number
  permissions?: Record<string, any>
  can_manage_all?: boolean
  can_manage_customers?: boolean
  can_manage_staff?: boolean
  can_manage_appointments?: boolean
  can_view_reports?: boolean
  managed_locations?: number[]
  managed_staff?: number[]
  managed_customers?: number[]
  is_active?: boolean
}

/**
 * Admin Manager Detail/Edit Page
 * Route: /ad/managers/[id] (Security: /ad/)
 */
export default function AdminManagerDetail() {
  const router = useRouter()
  const params = useParams()
  const managerId = params.id as string

  const [manager, setManager] = useState<Manager | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    can_manage_all: false,
    can_manage_customers: false,
    can_manage_staff: false,
    can_manage_appointments: true,
    can_view_reports: true,
    is_active: true,
  })

  useEffect(() => {
    if (managerId === 'new') {
      setLoading(false)
    } else {
      fetchManager()
    }
  }, [managerId])

  const fetchManager = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<ManagerDetailResponse>(
        ADMIN_ENDPOINTS.MANAGERS.UPDATE(parseInt(managerId))
      )
      
      if (response.data.success && response.data.data) {
        const managerData = response.data.data
        setManager(managerData)
        setFormData({
          can_manage_all: managerData.can_manage_all,
          can_manage_customers: managerData.can_manage_customers,
          can_manage_staff: managerData.can_manage_staff,
          can_manage_appointments: managerData.can_manage_appointments,
          can_view_reports: managerData.can_view_reports,
          is_active: managerData.is_active,
        })
      } else {
        setError('Failed to load manager')
      }
    } catch (err: any) {
      const status = err.response?.status
      if (status === 404) {
        setError(`Manager with ID ${managerId} not found`)
      } else {
        setError(err.response?.data?.error?.message || 'Failed to load manager')
      }
      console.error('Error fetching manager:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    try {
      setSaving(true)
      
      const updateData: ManagerUpdateRequest = {
        ...formData,
      }
      
      await apiClient.put(ADMIN_ENDPOINTS.MANAGERS.UPDATE(parseInt(managerId)), updateData)
      
      // Refresh manager data
      await fetchManager()
      
      alert('Manager updated successfully')
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to update manager')
      console.error('Error updating manager:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this manager? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.MANAGERS.DELETE(parseInt(managerId)))
      router.push('/ad/managers')
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete manager')
      console.error('Error deleting manager:', err)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading manager...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  if (!manager && managerId !== 'new') {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-destructive mb-4">{error || 'Manager not found'}</p>
              <Button onClick={() => router.push('/ad/managers')}>
                Back to Managers
              </Button>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  const displayName = manager?.user.first_name && manager?.user.last_name
    ? `${manager.user.first_name} ${manager.user.last_name}`
    : manager?.user.email || 'New Manager'

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">{displayName}</h1>
              <p className="text-muted-foreground">
                {managerId === 'new' ? 'Create a new manager' : 'View and manage manager permissions'}
              </p>
            </div>
            {managerId !== 'new' && manager && (
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => router.push('/ad/managers')}>
                  Back to List
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  Delete Manager
                </Button>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              <div className="flex items-center justify-between">
                <p>{error}</p>
                <Button variant="outline" size="sm" onClick={() => router.push('/ad/managers')}>
                  Back to List
                </Button>
              </div>
            </div>
          )}

          {/* Manager Info */}
          {manager && (
            <div className="mb-6 p-4 bg-muted rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Email:</span>
                  <span className="ml-2 font-medium">{manager.user.email}</span>
                </div>
                {manager.user.username && (
                  <div>
                    <span className="text-muted-foreground">Username:</span>
                    <span className="ml-2 font-medium">{manager.user.username}</span>
                  </div>
                )}
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    manager.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {manager.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {manager.created_at && (
                  <div>
                    <span className="text-muted-foreground">Created:</span>
                    <span className="ml-2">
                      {new Date(manager.created_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Permissions Form */}
          <form onSubmit={handleSave} className="space-y-6">
            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-xl font-semibold mb-4">Permissions</h2>
              
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="can_manage_all"
                    checked={formData.can_manage_all}
                    onChange={(e) => {
                      const checked = e.target.checked
                      setFormData(prev => ({
                        ...prev,
                        can_manage_all: checked,
                        // If full access is enabled, enable all permissions
                        ...(checked ? {
                          can_manage_customers: true,
                          can_manage_staff: true,
                          can_manage_appointments: true,
                          can_view_reports: true,
                        } : {})
                      }))
                    }}
                    className="w-4 h-4"
                  />
                  <label htmlFor="can_manage_all" className="text-sm font-medium">
                    Full Access (Can manage all resources)
                  </label>
                </div>

                <div className="pl-6 space-y-3 border-l-2 ml-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="can_manage_customers"
                      checked={formData.can_manage_customers}
                      onChange={(e) => setFormData(prev => ({ ...prev, can_manage_customers: e.target.checked }))}
                      disabled={formData.can_manage_all}
                      className="w-4 h-4"
                    />
                    <label htmlFor="can_manage_customers" className="text-sm font-medium">
                      Manage Customers
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="can_manage_staff"
                      checked={formData.can_manage_staff}
                      onChange={(e) => setFormData(prev => ({ ...prev, can_manage_staff: e.target.checked }))}
                      disabled={formData.can_manage_all}
                      className="w-4 h-4"
                    />
                    <label htmlFor="can_manage_staff" className="text-sm font-medium">
                      Manage Staff
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="can_manage_appointments"
                      checked={formData.can_manage_appointments}
                      onChange={(e) => setFormData(prev => ({ ...prev, can_manage_appointments: e.target.checked }))}
                      disabled={formData.can_manage_all}
                      className="w-4 h-4"
                    />
                    <label htmlFor="can_manage_appointments" className="text-sm font-medium">
                      Manage Appointments
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="can_view_reports"
                      checked={formData.can_view_reports}
                      onChange={(e) => setFormData(prev => ({ ...prev, can_view_reports: e.target.checked }))}
                      disabled={formData.can_manage_all}
                      className="w-4 h-4"
                    />
                    <label htmlFor="can_view_reports" className="text-sm font-medium">
                      View Reports
                    </label>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-4 border-t">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="w-4 h-4"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium">
                    Manager is active
                  </label>
                </div>
              </div>

              {/* Managed Resources Info */}
              {manager && (
                <div className="pt-4 border-t mt-4">
                  <h3 className="text-sm font-semibold mb-2">Managed Resources</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Staff:</span>
                      <span className="ml-2 font-medium">
                        {manager.managed_staff?.length || 0}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Customers:</span>
                      <span className="ml-2 font-medium">
                        {manager.managed_customers?.length || 0}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    <strong>Why 0?</strong> No customers or staff are assigned to this manager yet. Assignments are done in Django admin (Managers → edit → Managed staff / Managed customers) or via API. A future update may add assignment from Staff or Customer pages.
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button type="submit" disabled={saving || managerId === 'new'}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
                {managerId !== 'new' && (
                  <Button type="button" variant="outline" onClick={() => router.push('/ad/managers')}>
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </form>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
