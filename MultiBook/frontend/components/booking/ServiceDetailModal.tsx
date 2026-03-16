'use client'

/**
 * Service Detail Modal Component
 * 
 * Displays detailed information about a service in a modal dialog.
 */
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { formatCurrency } from '@/lib/utils'

interface ServiceDetail {
  id: number
  name: string
  slug?: string
  description?: string
  duration: number
  price: string | number
  currency?: string
  image?: string
  color?: string
  category?: {
    id: number
    name: string
    description?: string
  }
  category_name?: string
  capacity?: number
  padding_time?: number
  is_active?: boolean
}

interface ServiceDetailModalProps {
  serviceId: number | null
  isOpen: boolean
  onClose: () => void
  /** Called when user chooses one-time booking */
  onSelect: (serviceId: number) => void
  /** Called when user chooses subscription (recurring). If provided, shows "Subscribe" option. */
  onSelectSubscription?: (serviceId: number) => void
}

export function ServiceDetailModal({
  serviceId,
  isOpen,
  onClose,
  onSelect,
  onSelectSubscription,
}: ServiceDetailModalProps) {
  const [service, setService] = useState<ServiceDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && serviceId) {
      fetchServiceDetail()
    } else {
      setService(null)
      setError(null)
    }
  }, [isOpen, serviceId])

  const fetchServiceDetail = async () => {
    if (!serviceId) return

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.get(`${PUBLIC_ENDPOINTS.SERVICES.LIST}${serviceId}/`)

      if (response.data.success && response.data.data) {
        setService(response.data.data)
      } else {
        setError(response.data.error?.message || 'Failed to load service details')
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error?.message || 
                          'Unable to load service details. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const handleSelectOneTime = () => {
    if (serviceId) {
      onSelect(serviceId)
      onClose()
    }
  }

  const handleSelectSubscription = () => {
    if (serviceId && onSelectSubscription) {
      onSelectSubscription(serviceId)
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-background border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Service Details</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-2xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading service details...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg mb-4">
              {error}
            </div>
          )}

          {service && !loading && (
            <>
              {/* Service Image */}
              {service.image && (
                <div className="mb-6">
                  <img
                    src={service.image}
                    alt={service.name}
                    className="w-full h-64 object-cover rounded-lg"
                  />
                </div>
              )}

              {/* Service Header */}
              <div className="mb-6">
                {service.category_name && (
                  <span className="inline-block text-xs text-muted-foreground uppercase tracking-wide mb-2">
                    {service.category_name}
                  </span>
                )}
                <h3 className="text-3xl font-bold mb-4">{service.name}</h3>
                
                {/* Price and Duration */}
                <div className="flex items-center gap-6 mb-4">
                  <div>
                    <span className="text-sm text-muted-foreground">Price</span>
                    <div className="text-3xl font-bold">
                      {formatCurrency(typeof service.price === 'string' ? parseFloat(service.price) : service.price)}
                    </div>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Duration</span>
                    <div className="text-xl font-semibold">
                      {service.duration} minutes
                    </div>
                  </div>
                </div>
              </div>

              {/* Description */}
              {service.description && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold mb-2">Description</h4>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {service.description}
                  </p>
                </div>
              )}

              {/* Service Details */}
              <div className="border-t pt-6 mb-6">
                <h4 className="text-lg font-semibold mb-4">Service Information</h4>
                <dl className="grid grid-cols-2 gap-4">
                  {service.capacity !== undefined && (
                    <>
                      <dt className="text-sm text-muted-foreground">Capacity</dt>
                      <dd className="text-sm font-medium">
                        {service.capacity} {service.capacity === 1 ? 'customer' : 'customers'} per booking
                      </dd>
                    </>
                  )}
                  {service.padding_time !== undefined && service.padding_time > 0 && (
                    <>
                      <dt className="text-sm text-muted-foreground">Padding Time</dt>
                      <dd className="text-sm font-medium">{service.padding_time} minutes</dd>
                    </>
                  )}
                  {service.currency && (
                    <>
                      <dt className="text-sm text-muted-foreground">Currency</dt>
                      <dd className="text-sm font-medium">{service.currency}</dd>
                    </>
                  )}
                </dl>
              </div>

              {/* Category Description */}
              {service.category?.description && (
                <div className="border-t pt-6 mb-6">
                  <h4 className="text-lg font-semibold mb-2">{service.category.name}</h4>
                  <p className="text-muted-foreground whitespace-pre-line">
                    {service.category.description}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col gap-3 pt-6 border-t">
                <div className="flex gap-4">
                  <button
                    onClick={onClose}
                    className="flex-1 px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSelectOneTime}
                    className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold"
                  >
                    Book one-time
                  </button>
                </div>
                {onSelectSubscription && (
                  <button
                    onClick={handleSelectSubscription}
                    className="w-full px-6 py-3 border-2 border-primary text-primary rounded-lg hover:bg-primary/10 transition-colors font-semibold"
                  >
                    Subscribe (weekly / every 2 weeks / monthly)
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}