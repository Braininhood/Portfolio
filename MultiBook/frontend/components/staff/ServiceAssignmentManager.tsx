'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS, PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import type { StaffService, StaffServiceCreateRequest } from '@/types/staff'

interface Service {
  id: number
  name: string
  price: number
  duration: number
}

interface ServiceAssignmentManagerProps {
  staffId: number
  services: StaffService[]
  onUpdate: () => void
}

export function ServiceAssignmentManager({ staffId, services, onUpdate }: ServiceAssignmentManagerProps) {
  const [localServices, setLocalServices] = useState<StaffService[]>(services)
  const [availableServices, setAvailableServices] = useState<Service[]>([])
  const [editingService, setEditingService] = useState<StaffService | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    service_id: 0,
    price_override: null as number | null,
    duration_override: null as number | null,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [loadingServices, setLoadingServices] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLocalServices(services)
    fetchAvailableServices()
  }, [services])

  const fetchAvailableServices = async () => {
    try {
      setLoadingServices(true)
      const response = await apiClient.get(PUBLIC_ENDPOINTS.SERVICES.LIST)
      if (response.data.success && response.data.data) {
        setAvailableServices(response.data.data)
      }
    } catch (err) {
      console.error('Error fetching services:', err)
    } finally {
      setLoadingServices(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.service_id) {
      setError('Please select a service')
      return
    }

    // Check if service is already assigned (excluding the one being edited)
    const existing = localServices.find(s => {
      const sId = s.service_id || s.service?.id
      return sId === formData.service_id && s.id !== editingService?.id
    })
    if (existing && !editingService) {
      setError('This service is already assigned to this staff member')
      return
    }

    try {
      setLoading(true)
      
      if (editingService?.id) {
        // Update existing assignment
        await apiClient.patch(
          ADMIN_ENDPOINTS.STAFF.SERVICES.UPDATE(editingService.id),
          {
            staff: staffId,
            service_id: formData.service_id,
            price_override: formData.price_override || null,
            duration_override: formData.duration_override || null,
            is_active: formData.is_active,
          }
        )
      } else {
        // Create new assignment
        const request: StaffServiceCreateRequest = {
          staff: staffId,
          service_id: formData.service_id,
          price_override: formData.price_override || null,
          duration_override: formData.duration_override || null,
          is_active: formData.is_active,
        }
        await apiClient.post(ADMIN_ENDPOINTS.STAFF.SERVICES.CREATE, request)
      }

      setFormData({ service_id: 0, price_override: null, duration_override: null, is_active: true })
      setShowForm(false)
      setEditingService(null)
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save service assignment')
      console.error('Error saving service assignment:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (service: StaffService) => {
    setEditingService(service)
    // Get service_id from either service.service_id or service.service.id
    const serviceId = service.service_id || service.service?.id || 0
    setFormData({
      service_id: serviceId,
      price_override: service.price_override || null,
      duration_override: service.duration_override || null,
      is_active: service.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this service assignment?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.SERVICES.DELETE(id))
      onUpdate()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete service assignment')
      console.error('Error deleting service assignment:', err)
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingService(null)
    setFormData({ service_id: 0, price_override: null, duration_override: null, is_active: true })
    setError(null)
  }

  const getServiceName = (serviceId: number | undefined) => {
    if (!serviceId) return 'Unknown Service'
    const service = availableServices.find(s => s.id === serviceId)
    return service?.name || 'Unknown Service'
  }

  const getServicePrice = (serviceId: number) => {
    const service = availableServices.find(s => s.id === serviceId)
    return service?.price || 0
  }

  const getServiceDuration = (serviceId: number) => {
    const service = availableServices.find(s => s.id === serviceId)
    return service?.duration || 0
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Service Assignments</h3>
          <p className="text-sm text-muted-foreground">
            Assign services to this staff member with optional price/duration overrides
          </p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)} size="sm">
            Assign Service
          </Button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="border rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Service</label>
            <select
              value={formData.service_id}
              onChange={(e) => {
                const serviceId = parseInt(e.target.value)
                setFormData(prev => ({
                  ...prev,
                  service_id: serviceId,
                  // Set defaults from service if not editing
                  price_override: editingService ? prev.price_override : null,
                  duration_override: editingService ? prev.duration_override : null,
                }))
              }}
              className="w-full px-3 py-2 border rounded-md"
              disabled={!!editingService}
              required
            >
              <option value={0}>Select a service</option>
              {availableServices.map(service => (
                <option key={service.id} value={service.id}>
                  {service.name} - £{service.price} ({service.duration} min)
                </option>
              ))}
            </select>
          </div>

          {formData.service_id > 0 && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Price Override (leave blank to use service default: £{getServicePrice(formData.service_id)})
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.price_override || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    price_override: e.target.value ? parseFloat(e.target.value) : null,
                  }))}
                  placeholder="Leave blank for default"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Duration Override (leave blank to use service default: {getServiceDuration(formData.service_id)} min)
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.duration_override || ''}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    duration_override: e.target.value ? parseInt(e.target.value) : null,
                  }))}
                  placeholder="Leave blank for default"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </>
          )}

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active_service"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="is_active_service" className="text-sm">
              Active
            </label>
          </div>

          {error && (
            <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading || loadingServices} size="sm">
              {editingService ? 'Update' : 'Assign'} Service
            </Button>
            <Button type="button" variant="outline" onClick={handleCancel} size="sm">
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Services List */}
      <div className="space-y-2">
        {localServices.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No services assigned. Assign one to get started.
          </p>
        ) : (
          localServices.map((service) => (
            <div
              key={service.id}
              className="flex items-center justify-between border rounded-lg p-3"
            >
              <div>
                <div className="font-medium">
                  {service.service_name || getServiceName(service.service_id || service.service?.id)}
                </div>
                <div className="text-sm text-muted-foreground">
                  Price: £{service.price_override ?? getServicePrice(service.service_id || service.service?.id)}
                  {' | '}
                  Duration: {service.duration_override ?? getServiceDuration(service.service_id || service.service?.id)} min
                  {!service.is_active && (
                    <span className="ml-2 text-destructive">(Inactive)</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(service)}
                >
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => service.id && handleDelete(service.id)}
                >
                  Remove
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
