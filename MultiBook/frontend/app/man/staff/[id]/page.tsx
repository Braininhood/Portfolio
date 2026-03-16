'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { MANAGER_ENDPOINTS } from '@/lib/api/endpoints'
import type { Staff, StaffDetailResponse } from '@/types/staff'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

/**
 * Manager Staff Detail Page (Read-Only)
 * Route: /man/staff/[id] (Security: /man/)
 */
export default function ManagerStaffDetail() {
  const router = useRouter()
  const params = useParams()
  const staffId = params.id as string

  const [staff, setStaff] = useState<Staff | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'info' | 'areas' | 'schedule' | 'services'>('info')

  useEffect(() => {
    fetchStaff()
  }, [staffId])

  const fetchStaff = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<StaffDetailResponse>(
        MANAGER_ENDPOINTS.STAFF.UPDATE(parseInt(staffId))
      )
      
      if (response.data.success && response.data.data) {
        setStaff(response.data.data)
      } else {
        setError('Failed to load staff member')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load staff member')
      console.error('Error fetching staff:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole={['admin', 'manager']}>
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading staff member...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requiredRole={['admin', 'manager']}>
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">{staff?.name || 'Staff Member'}</h1>
              <p className="text-muted-foreground">View staff member details (read-only)</p>
            </div>
            <Button variant="outline" onClick={() => router.push('/man/staff')}>
              Back to List
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 border-b">
            <button
              onClick={() => setActiveTab('info')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'info'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Basic Info
            </button>
            <button
              onClick={() => setActiveTab('areas')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'areas'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Service Areas
            </button>
            <button
              onClick={() => setActiveTab('schedule')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'schedule'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Schedule
            </button>
            <button
              onClick={() => setActiveTab('services')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'services'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Services
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {/* Basic Info Tab */}
          {activeTab === 'info' && staff && (
            <div className="border rounded-lg p-6 space-y-4">
              <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
              
              <div>
                <label className="block text-sm font-medium mb-2">Name</label>
                <div className="px-3 py-2 bg-muted rounded-md">{staff.name}</div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <div className="px-3 py-2 bg-muted rounded-md">{staff.email}</div>
              </div>

              {staff.phone && (
                <div>
                  <label className="block text-sm font-medium mb-2">Phone</label>
                  <div className="px-3 py-2 bg-muted rounded-md">{staff.phone}</div>
                </div>
              )}

              {staff.bio && (
                <div>
                  <label className="block text-sm font-medium mb-2">Bio</label>
                  <div className="px-3 py-2 bg-muted rounded-md whitespace-pre-wrap">{staff.bio}</div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Status</label>
                <div className="px-3 py-2 bg-muted rounded-md">
                  {staff.is_active ? 'Active' : 'Inactive'}
                </div>
              </div>
            </div>
          )}

          {/* Service Areas Tab */}
          {activeTab === 'areas' && staff && (
            <div className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Service Areas</h2>
              {staff.service_areas && staff.service_areas.length > 0 ? (
                <div className="space-y-2">
                  {staff.service_areas.map((area) => (
                    <div key={area.id} className="border rounded-lg p-3">
                      <div className="font-medium">{area.postcode}</div>
                      <div className="text-sm text-muted-foreground">
                        Radius: {area.radius_miles} miles
                        {!area.is_active && <span className="ml-2 text-destructive">(Inactive)</span>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No service areas defined</p>
              )}
            </div>
          )}

          {/* Schedule Tab */}
          {activeTab === 'schedule' && staff && (
            <div className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Weekly Schedule</h2>
              {staff.schedules && staff.schedules.length > 0 ? (
                <div className="space-y-2">
                  {staff.schedules.map((schedule) => (
                    <div key={schedule.id} className="border rounded-lg p-3">
                      <div className="font-medium">{schedule.day_name || `Day ${schedule.day_of_week}`}</div>
                      <div className="text-sm text-muted-foreground">
                        {schedule.start_time} - {schedule.end_time}
                        {schedule.breaks && schedule.breaks.length > 0 && (
                          <span className="ml-2">
                            ({schedule.breaks.length} break{schedule.breaks.length !== 1 ? 's' : ''})
                          </span>
                        )}
                        {!schedule.is_active && (
                          <span className="ml-2 text-destructive">(Inactive)</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No schedule configured</p>
              )}
            </div>
          )}

          {/* Services Tab */}
          {activeTab === 'services' && staff && (
            <div className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Service Assignments</h2>
              {staff.services && staff.services.length > 0 ? (
                <div className="space-y-2">
                  {staff.services.map((service) => (
                    <div key={service.id} className="border rounded-lg p-3">
                      <div className="font-medium">
                        {service.service_name || `Service ${service.service_id}`}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Price: £{service.price_override ?? 'Default'} | Duration: {service.duration_override ?? 'Default'} min
                        {!service.is_active && (
                          <span className="ml-2 text-destructive">(Inactive)</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No services assigned</p>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
