'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface Manager {
  id: number
  user: {
    id: number
    email: string
    first_name?: string
    last_name?: string
  }
  can_manage_all: boolean
  can_manage_customers: boolean
  can_manage_staff: boolean
  can_manage_appointments: boolean
  can_view_reports: boolean
  is_active: boolean
  managed_staff?: number[]
  managed_customers?: number[]
}

interface ManagerListResponse {
  success: boolean
  data: Manager[]
  meta: {
    count: number
  }
}

/**
 * Admin Managers List Page
 * Route: /ad/managers (Security: /ad/)
 */
export default function AdminManagersList() {
  const router = useRouter()
  const [managers, setManagers] = useState<Manager[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterActive, setFilterActive] = useState<boolean | null>(null)

  useEffect(() => {
    fetchManagers()
  }, [filterActive])

  const fetchManagers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (filterActive !== null) {
        params.append('is_active', filterActive.toString())
      }
      
      const url = `${ADMIN_ENDPOINTS.MANAGERS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<ManagerListResponse>(url)
      
      if (response.data.success && response.data.data) {
        setManagers(response.data.data)
      } else {
        setError('Failed to load managers')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load managers')
      console.error('Error fetching managers:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this manager? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.MANAGERS.DELETE(id))
      fetchManagers() // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete manager')
      console.error('Error deleting manager:', err)
    }
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Manager Management</h1>
              <p className="text-muted-foreground">
                Manage managers and their permissions
              </p>
            </div>
            <Button onClick={() => router.push('/ad/register?role=manager')}>
              Add New Manager
            </Button>
          </div>

          {/* Filters */}
          <div className="mb-6 flex gap-4">
            <Button
              variant={filterActive === null ? 'default' : 'outline'}
              onClick={() => setFilterActive(null)}
            >
              All
            </Button>
            <Button
              variant={filterActive === true ? 'default' : 'outline'}
              onClick={() => setFilterActive(true)}
            >
              Active
            </Button>
            <Button
              variant={filterActive === false ? 'default' : 'outline'}
              onClick={() => setFilterActive(false)}
            >
              Inactive
            </Button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading managers...</p>
            </div>
          )}

          {/* Managers List */}
          {!loading && !error && (
            <div className="space-y-4">
              {managers.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p className="text-lg mb-2">No managers found</p>
                  <Button onClick={() => router.push('/ad/register?role=manager')} variant="outline">
                    Add First Manager
                  </Button>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {managers.map((manager) => {
                    const displayName = manager.user.first_name && manager.user.last_name
                      ? `${manager.user.first_name} ${manager.user.last_name}`
                      : manager.user.email
                    return (
                      <div
                        key={manager.id}
                        className="border rounded-lg p-6 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h3 className="text-xl font-semibold mb-1">{displayName}</h3>
                            <p className="text-sm text-muted-foreground">{manager.user.email}</p>
                          </div>
                          <span
                            className={`px-2 py-1 text-xs rounded ${
                              manager.is_active
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {manager.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>

                        {/* Permissions */}
                        <div className="mb-4 space-y-1 text-sm">
                          {manager.can_manage_all && (
                            <div className="text-muted-foreground">✓ Full Access</div>
                          )}
                          {!manager.can_manage_all && (
                            <>
                              {manager.can_manage_customers && (
                                <div className="text-muted-foreground">✓ Manage Customers</div>
                              )}
                              {manager.can_manage_staff && (
                                <div className="text-muted-foreground">✓ Manage Staff</div>
                              )}
                              {manager.can_manage_appointments && (
                                <div className="text-muted-foreground">✓ Manage Appointments</div>
                              )}
                              {manager.can_view_reports && (
                                <div className="text-muted-foreground">✓ View Reports</div>
                              )}
                            </>
                          )}
                        </div>

                        {/* Managed Resources Count */}
                        {(manager.managed_staff?.length || manager.managed_customers?.length) && (
                          <div className="mb-4 text-sm text-muted-foreground">
                            {manager.managed_staff?.length || 0} staff, {manager.managed_customers?.length || 0} customers
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-2 mt-4">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={() => router.push(`/ad/managers/${manager.id}`)}
                          >
                            View/Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(manager.id)}
                          >
                            Delete
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
