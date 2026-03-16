'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { StaffAreaManager } from '@/components/staff/StaffAreaManager'
import { ScheduleEditor } from '@/components/staff/ScheduleEditor'
import { ServiceAssignmentManager } from '@/components/staff/ServiceAssignmentManager'
import { StaffPerformanceMetrics } from '@/components/staff/StaffPerformanceMetrics'
import { StaffCalendarIntegration } from '@/components/staff/StaffCalendarIntegration'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Staff, StaffDetailResponse, StaffUpdateRequest } from '@/types/staff'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

/**
 * Admin Staff Detail/Edit Page
 * Route: /ad/staff/[id] (Security: /ad/)
 */
export default function AdminStaffDetail() {
  const router = useRouter()
  const params = useParams()
  const staffId = params.id as string

  const [staff, setStaff] = useState<Staff | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'info' | 'areas' | 'schedule' | 'services' | 'performance' | 'calendar'>('info')

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    bio: '',
    is_active: true,
    user: null as number | null,
  })

  useEffect(() => {
      if (staffId === 'new') {
        // New staff - initialize empty form
        setFormData({
          name: '',
          email: '',
          phone: '',
          bio: '',
          is_active: true,
          user: null,
        })
      setLoading(false)
    } else {
      fetchStaff()
    }
  }, [staffId])

  const fetchStaff = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<StaffDetailResponse>(
        ADMIN_ENDPOINTS.STAFF.UPDATE(parseInt(staffId))
      )
      
      if (response.data.success && response.data.data) {
        const staffData = response.data.data
        setStaff(staffData)
        const userId = staffData.user != null
          ? (typeof staffData.user === 'object' && staffData.user !== null && 'id' in staffData.user
            ? (staffData.user as { id: number }).id
            : staffData.user)
          : null
        setFormData({
          name: staffData.name,
          email: staffData.email,
          phone: staffData.phone || '',
          bio: staffData.bio || '',
          is_active: staffData.is_active,
          user: userId ?? null,
        })
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

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim() || !formData.email.trim()) {
      setError('Name and email are required')
      return
    }

    try {
      setSaving(true)
      
      if (staffId === 'new') {
        // Create new staff
        const response = await apiClient.post(ADMIN_ENDPOINTS.STAFF.CREATE, formData)
        if (response.data.success && response.data.data) {
          router.push(`/ad/staff/${response.data.data.id}`)
        }
      } else {
        // Update existing staff (include user for link/unlink)
        const updateData: StaffUpdateRequest = {
          name: formData.name,
          email: formData.email,
          phone: formData.phone || undefined,
          bio: formData.bio || undefined,
          is_active: formData.is_active,
          user: formData.user ?? undefined,
        }
        await apiClient.patch(ADMIN_ENDPOINTS.STAFF.UPDATE(parseInt(staffId)), updateData)
        fetchStaff() // Refresh data
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save staff member')
      console.error('Error saving staff:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this staff member? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.DELETE(parseInt(staffId)))
      router.push('/ad/staff')
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete staff member')
      console.error('Error deleting staff:', err)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="admin">
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
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {staffId === 'new' ? 'Add New Staff Member' : staff?.name || 'Staff Member'}
              </h1>
              <p className="text-muted-foreground">
                {staffId === 'new' 
                  ? 'Create a new staff member' 
                  : 'Manage staff member details, schedules, and service areas'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push('/ad/staff')}>
                Back to List
              </Button>
              {staffId !== 'new' && (
                <Button variant="destructive" onClick={handleDelete}>
                  Delete
                </Button>
              )}
            </div>
          </div>

          {/* Tabs */}
          {staffId !== 'new' && (
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
              <button
                onClick={() => setActiveTab('performance')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'performance'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Performance
              </button>
              <button
                onClick={() => setActiveTab('calendar')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'calendar'
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Calendar
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {/* Basic Info Tab */}
          {(activeTab === 'info' || staffId === 'new') && (
            <form onSubmit={handleSave} className="space-y-6">
              <div className="border rounded-lg p-6 space-y-4">
                <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="e.g., +44 20 1234 5678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Bio</label>
                  <textarea
                    value={formData.bio}
                    onChange={(e) => setFormData(prev => ({ ...prev, bio: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    rows={4}
                    placeholder="Staff member biography..."
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded"
                  />
                  <label htmlFor="is_active" className="text-sm">
                    Active (available for booking)
                  </label>
                </div>

                {/* Link user account (for staff portal login & calendar sync) */}
                {staffId !== 'new' && staff && (
                  <div className="border-t pt-6 mt-6">
                    <h3 className="text-sm font-semibold mb-2">User account (portal login &amp; calendar)</h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Linking a user lets this staff member log in to the staff portal and connect Google/Outlook calendar. Create the user first (e.g. staff register or Django admin) then link by User ID.
                    </p>
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="text-sm">
                        Current: <strong>{staff.user_email || 'Not linked'}</strong>
                      </span>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min={1}
                          placeholder="User ID"
                          value={formData.user ?? ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, user: e.target.value ? parseInt(e.target.value, 10) : null }))}
                          className="w-24 px-2 py-1 border rounded text-sm"
                        />
                        <span className="text-xs text-muted-foreground">Enter User ID and click Save below to link.</span>
                        {(staff.user != null || formData.user != null) && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() => setFormData(prev => ({ ...prev, user: null }))}
                          >
                            Unlink (then click Save)
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Saving...' : staffId === 'new' ? 'Create Staff Member' : 'Save Changes'}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => router.push('/ad/staff')}>
                    Cancel
                  </Button>
                </div>
              </div>
            </form>
          )}

          {/* Service Areas Tab */}
          {activeTab === 'areas' && staff && (
            <div className="border rounded-lg p-6">
              <StaffAreaManager
                staffId={staff.id}
                areas={staff.service_areas || []}
                onUpdate={fetchStaff}
              />
            </div>
          )}

          {/* Schedule Tab */}
          {activeTab === 'schedule' && staff && (
            <div className="border rounded-lg p-6">
              <ScheduleEditor
                staffId={staff.id}
                schedules={staff.schedules || []}
                onUpdate={fetchStaff}
              />
            </div>
          )}

          {/* Services Tab */}
          {activeTab === 'services' && staff && (
            <div className="border rounded-lg p-6">
              <ServiceAssignmentManager
                staffId={staff.id}
                services={staff.services || []}
                onUpdate={fetchStaff}
              />
            </div>
          )}

          {/* Performance Tab */}
          {activeTab === 'performance' && staff && (
            <div className="border rounded-lg p-6">
              <StaffPerformanceMetrics staffId={staff.id} />
            </div>
          )}

          {/* Calendar Tab */}
          {activeTab === 'calendar' && staff && (
            <div className="border rounded-lg p-6">
              <StaffCalendarIntegration 
                staffId={staff.id}
                staffUserId={staff.user}
              />
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
