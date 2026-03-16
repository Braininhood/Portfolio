'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { ServiceStaffAssignments } from '@/components/service/ServiceStaffAssignments'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Service, ServiceDetailResponse, ServiceUpdateRequest, Category, CategoryListResponse } from '@/types/service'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

/**
 * Admin Service Detail/Edit Page
 * Route: /ad/services/[id] (Security: /ad/)
 */
export default function AdminServiceDetail() {
  const router = useRouter()
  const params = useParams()
  const serviceId = params.id as string

  const [service, setService] = useState<Service | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'info' | 'staff'>('info')

  const [formData, setFormData] = useState({
    category_id: 0,
    name: '',
    description: '',
    duration: 60,
    price: '',
    currency: 'GBP',
    color: '#3B82F6',
    capacity: 1,
    padding_time: 0,
    position: 0,
    is_active: true,
  })

  useEffect(() => {
    fetchCategories()
    if (serviceId === 'new') {
      setLoading(false)
    } else {
      fetchService()
    }
  }, [serviceId])

  const fetchCategories = async () => {
    try {
      const response = await apiClient.get<CategoryListResponse>(ADMIN_ENDPOINTS.CATEGORIES.LIST)
      if (response.data.success && response.data.data) {
        setCategories(response.data.data)
        if (serviceId === 'new' && response.data.data.length > 0) {
          setFormData(prev => ({ ...prev, category_id: response.data.data[0].id }))
        }
      }
    } catch (err: any) {
      console.error('Error fetching categories:', err)
    }
  }

  const fetchService = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<ServiceDetailResponse>(
        ADMIN_ENDPOINTS.SERVICES.UPDATE(parseInt(serviceId))
      )
      
      if (response.data.success && response.data.data) {
        const serviceData = response.data.data
        setService(serviceData)
        setFormData({
          category_id: serviceData.category_id,
          name: serviceData.name,
          description: serviceData.description || '',
          duration: serviceData.duration,
          price: serviceData.price.toString(),
          currency: serviceData.currency,
          color: serviceData.color,
          capacity: serviceData.capacity,
          padding_time: serviceData.padding_time,
          position: serviceData.position,
          is_active: serviceData.is_active,
        })
      } else {
        setError('Failed to load service')
      }
    } catch (err: any) {
      const status = err.response?.status
      if (status === 404) {
        setError(`Service with ID ${serviceId} not found`)
      } else {
        setError(err.response?.data?.error?.message || 'Failed to load service')
      }
      console.error('Error fetching service:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim() || !formData.category_id) {
      setError('Name and category are required')
      return
    }

    if (!formData.price || parseFloat(formData.price.toString()) <= 0) {
      setError('Price must be greater than 0')
      return
    }

    try {
      setSaving(true)
      
      const updateData: ServiceUpdateRequest = {
        ...formData,
        price: parseFloat(formData.price.toString()),
      }
      
      if (serviceId === 'new') {
        // Create new service
        const response = await apiClient.post(ADMIN_ENDPOINTS.SERVICES.CREATE, updateData)
        if (response.data.success) {
          router.push(`/ad/services/${response.data.data.id}`)
        } else {
          setError('Failed to create service')
        }
      } else {
        // Update existing service
        const response = await apiClient.patch(
          ADMIN_ENDPOINTS.SERVICES.UPDATE(parseInt(serviceId)),
          updateData
        )
        if (response.data.success) {
          setService(response.data.data)
          setError(null)
        } else {
          setError('Failed to update service')
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save service')
      console.error('Error saving service:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this service? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.SERVICES.DELETE(parseInt(serviceId)))
      router.push('/ad/services')
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete service')
      console.error('Error deleting service:', err)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading service...</p>
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
                {serviceId === 'new' ? 'New Service' : service?.name || 'Service'}
              </h1>
              <p className="text-muted-foreground">
                {serviceId === 'new' ? 'Create a new service' : 'View and manage service details'}
              </p>
            </div>
            {serviceId !== 'new' && service && (
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => router.push('/ad/services')}>
                  Back to List
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  Delete Service
                </Button>
              </div>
            )}
          </div>

          {/* Tabs */}
          {serviceId !== 'new' && service && (
            <div className="border-b mb-6">
              <div className="flex gap-4">
                <button
                  onClick={() => setActiveTab('info')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'info'
                      ? 'border-b-2 border-primary text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Info
                </button>
                <button
                  onClick={() => setActiveTab('staff')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'staff'
                      ? 'border-b-2 border-primary text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Staff Assignments
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              <div className="flex items-center justify-between">
                <p>{error}</p>
                <Button variant="outline" size="sm" onClick={() => router.push('/ad/services')}>
                  Back to List
                </Button>
              </div>
            </div>
          )}

          {/* Info Tab */}
          {(activeTab === 'info' || serviceId === 'new') && (
            <form onSubmit={handleSave} className="space-y-6">
              <div className="border rounded-lg p-6 space-y-4">
                <h2 className="text-xl font-semibold mb-4">Service Information</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Category *</label>
                    <select
                      value={formData.category_id}
                      onChange={(e) => setFormData(prev => ({ ...prev, category_id: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border rounded-md"
                      required
                    >
                      <option value="0">Select Category</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>

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
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                    rows={4}
                    placeholder="Service description..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Price *</label>
                    <div className="flex gap-2">
                      <select
                        value={formData.currency}
                        onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                        className="px-3 py-2 border rounded-md"
                      >
                        <option value="GBP">£</option>
                        <option value="USD">$</option>
                        <option value="EUR">€</option>
                      </select>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.price}
                        onChange={(e) => setFormData(prev => ({ ...prev, price: e.target.value }))}
                        className="flex-1 px-3 py-2 border rounded-md"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Duration (minutes) *</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.duration}
                      onChange={(e) => setFormData(prev => ({ ...prev, duration: parseInt(e.target.value) || 0 }))}
                      className="w-full px-3 py-2 border rounded-md"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Color</label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={formData.color}
                        onChange={(e) => setFormData(prev => ({ ...prev, color: e.target.value }))}
                        className="h-10 w-20 border rounded-md"
                      />
                      <input
                        type="text"
                        value={formData.color}
                        onChange={(e) => setFormData(prev => ({ ...prev, color: e.target.value }))}
                        className="flex-1 px-3 py-2 border rounded-md font-mono text-sm"
                        placeholder="#3B82F6"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Capacity</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.capacity}
                      onChange={(e) => setFormData(prev => ({ ...prev, capacity: parseInt(e.target.value) || 1 }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Padding Time (minutes)</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.padding_time}
                      onChange={(e) => setFormData(prev => ({ ...prev, padding_time: parseInt(e.target.value) || 0 }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Position</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.position}
                      onChange={(e) => setFormData(prev => ({ ...prev, position: parseInt(e.target.value) || 0 }))}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="Display order (lower = first)"
                    />
                  </div>

                  <div className="flex items-center gap-2 pt-6">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                      className="w-4 h-4"
                    />
                    <label className="text-sm font-medium">Service is active</label>
                  </div>
                </div>

                {service && (
                  <div className="pt-4 border-t">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Slug:</span>
                        <span className="ml-2 font-mono">{service.slug}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Created:</span>
                        <span className="ml-2">
                          {service.created_at ? new Date(service.created_at).toLocaleDateString() : '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Saving...' : serviceId === 'new' ? 'Create Service' : 'Save Changes'}
                  </Button>
                  {serviceId !== 'new' && (
                    <Button type="button" variant="outline" onClick={() => router.push('/ad/services')}>
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            </form>
          )}

          {/* Staff Assignments Tab */}
          {activeTab === 'staff' && service && (
            <ServiceStaffAssignments serviceId={service.id!} />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
