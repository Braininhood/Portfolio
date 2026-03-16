'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Staff, StaffListResponse } from '@/types/staff'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
/**
 * Admin Staff List Page
 * Route: /ad/staff (Security: /ad/)
 */
export default function AdminStaffList() {
  const router = useRouter()
  const [staff, setStaff] = useState<Staff[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterActive, setFilterActive] = useState<boolean | null>(null)

  useEffect(() => {
    fetchStaff()
  }, [filterActive])

  const fetchStaff = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (filterActive !== null) {
        params.append('is_active', filterActive.toString())
      }
      
      const url = `${ADMIN_ENDPOINTS.STAFF.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<StaffListResponse>(url)
      
      if (response.data.success && response.data.data) {
        setStaff(response.data.data)
      } else {
        setError('Failed to load staff')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load staff')
      console.error('Error fetching staff:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this staff member?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.DELETE(id))
      fetchStaff() // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete staff')
      console.error('Error deleting staff:', err)
    }
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Staff Management</h1>
              <p className="text-muted-foreground">
                Manage staff members, schedules, and service areas
              </p>
            </div>
            <Button onClick={() => router.push('/ad/staff/new')}>
              Add New Staff
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
              <p className="mt-4 text-muted-foreground">Loading staff...</p>
            </div>
          )}

          {/* Staff List */}
          {!loading && !error && (
            <div className="space-y-4">
              {staff.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p className="text-lg mb-2">No staff members found</p>
                  <Button onClick={() => router.push('/ad/staff/new')} variant="outline">
                    Add First Staff Member
                  </Button>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {staff.map((member) => (
                    <div
                      key={member.id}
                      className="border rounded-lg p-6 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold mb-1">{member.name}</h3>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                          {member.phone && (
                            <p className="text-sm text-muted-foreground">{member.phone}</p>
                          )}
                        </div>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            member.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {member.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>

                      {/* Service Areas Count */}
                      {member.service_areas && member.service_areas.length > 0 && (
                        <div className="mb-4 text-sm text-muted-foreground">
                          {member.service_areas.length} service area
                          {member.service_areas.length !== 1 ? 's' : ''}
                        </div>
                      )}

                      {/* Services Count */}
                      {member.services && member.services.length > 0 && (
                        <div className="mb-4 text-sm text-muted-foreground">
                          {member.services.length} service
                          {member.services.length !== 1 ? 's' : ''} assigned
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 mt-4">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => router.push(`/ad/staff/${member.id}`)}
                        >
                          View/Edit
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(member.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
