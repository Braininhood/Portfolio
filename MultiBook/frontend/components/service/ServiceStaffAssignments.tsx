'use client'

import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { StaffService, Staff } from '@/types/staff'
import { useEffect, useState } from 'react'

interface ServiceStaffAssignmentsProps {
  serviceId: number
}

export function ServiceStaffAssignments({ serviceId }: ServiceStaffAssignmentsProps) {
  const [staffServices, setStaffServices] = useState<StaffService[]>([])
  const [availableStaff, setAvailableStaff] = useState<Staff[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStaffId, setSelectedStaffId] = useState<number>(0)

  useEffect(() => {
    fetchStaffServices()
    fetchAvailableStaff()
  }, [serviceId])

  const fetchStaffServices = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get(
        `${ADMIN_ENDPOINTS.STAFF.SERVICES.LIST()}?service_id=${serviceId}`
      )
      
      if (response.data.success && response.data.data) {
        setStaffServices(response.data.data)
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load staff assignments')
      console.error('Error fetching staff services:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchAvailableStaff = async () => {
    try {
      const response = await apiClient.get(ADMIN_ENDPOINTS.STAFF.LIST)
      if (response.data.success && response.data.data) {
        setAvailableStaff(response.data.data.filter((s: Staff) => s.is_active))
      }
    } catch (err: any) {
      console.error('Error fetching staff:', err)
    }
  }

  const handleAssign = async () => {
    if (!selectedStaffId) return

    try {
      setError(null)
      
      await apiClient.post(ADMIN_ENDPOINTS.STAFF.SERVICES.CREATE, {
        staff: selectedStaffId,
        service_id: serviceId,
        is_active: true,
      })
      
      setSelectedStaffId(0)
      fetchStaffServices()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to assign staff')
      console.error('Error assigning staff:', err)
    }
  }

  const handleToggleActive = async (staffServiceId: number, isActive: boolean) => {
    try {
      await apiClient.patch(ADMIN_ENDPOINTS.STAFF.SERVICES.UPDATE(staffServiceId), {
        is_active: !isActive,
      })
      fetchStaffServices()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to update assignment')
      console.error('Error updating assignment:', err)
    }
  }

  const handleRemove = async (staffServiceId: number) => {
    if (!confirm('Are you sure you want to remove this staff assignment?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.SERVICES.DELETE(staffServiceId))
      fetchStaffServices()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to remove assignment')
      console.error('Error removing assignment:', err)
    }
  }

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading staff assignments...</div>
  }

  return (
    <div className="space-y-6">
      {/* Assign New Staff */}
      <div className="bg-card border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Assign Staff to Service</h3>
        <div className="flex gap-2">
          <select
            value={selectedStaffId}
            onChange={(e) => setSelectedStaffId(parseInt(e.target.value))}
            className="flex-1 px-3 py-2 border rounded-md"
          >
            <option value="0">Select Staff Member</option>
            {availableStaff
              .filter(staff => !staffServices.some(ss => ss.staff === staff.id))
              .map((staff) => (
                <option key={staff.id} value={staff.id}>
                  {staff.name} ({staff.email})
                </option>
              ))}
          </select>
          <Button onClick={handleAssign} disabled={!selectedStaffId}>
            Assign
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
          {error}
        </div>
      )}

      {/* Assigned Staff List */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Assigned Staff</h3>
        {staffServices.length > 0 ? (
          <div className="bg-card border rounded-lg overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Staff Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Price Override</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Duration Override</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {staffServices.map((ss) => {
                  // Find staff name from availableStaff
                  const staff = availableStaff.find(s => s.id === ss.staff)
                  return (
                    <tr key={ss.id}>
                      <td className="px-4 py-3">{staff?.name || 'N/A'}</td>
                      <td className="px-4 py-3">{staff?.email || '-'}</td>
                      <td className="px-4 py-3">
                        {ss.price_override ? `£${parseFloat(ss.price_override.toString()).toFixed(2)}` : '-'}
                      </td>
                      <td className="px-4 py-3">
                        {ss.duration_override ? `${ss.duration_override}m` : '-'}
                      </td>
                      <td className="px-4 py-3">
                        {ss.is_active ? (
                          <span className="text-green-600">Active</span>
                        ) : (
                          <span className="text-muted-foreground">Inactive</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleActive(ss.id!, ss.is_active)}
                          >
                            {ss.is_active ? 'Deactivate' : 'Activate'}
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleRemove(ss.id!)}
                          >
                            Remove
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            No staff assigned to this service
          </div>
        )}
      </div>
    </div>
  )
}
