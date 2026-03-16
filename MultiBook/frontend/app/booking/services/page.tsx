'use client'

/**
 * Booking Step 2: Service Selection
 * Route: /booking/services (Public - Guest Checkout)
 * 
 * Shows services available in the selected postcode area.
 */
import { useBookingStore } from '@/store/booking-store'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { formatCurrency } from '@/lib/utils'
import { ServiceDetailModal } from '@/components/booking/ServiceDetailModal'

interface Service {
  id: number
  name: string
  slug?: string
  duration: number  // Duration in minutes
  price: string | number
  currency?: string
  image?: string
  color?: string
  category_name?: string
  is_active?: boolean
  available_staff_count?: number
}

export default function ServicesPage() {
  const router = useRouter()
  const { postcode, setSelectedService, setBookingType } = useBookingStore()
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  useEffect(() => {
    if (!postcode) {
      router.push('/booking/postcode')
      return
    }

    // Fetch services available in this postcode area
    const fetchServices = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const response = await apiClient.get(PUBLIC_ENDPOINTS.SERVICES.BY_POSTCODE, {
          params: { postcode }
        })

        if (response.data.success && response.data.data) {
          setServices(response.data.data)
        } else {
          setError(response.data.error?.message || 'Failed to load services')
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.error?.message || 
                            'Unable to load services. Please try again.'
        setError(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    fetchServices()
  }, [postcode, router])

  const handleServiceClick = (serviceId: number) => {
    setSelectedServiceId(serviceId)
    setIsModalOpen(true)
  }

  const handleServiceSelect = (serviceId: number) => {
    setBookingType('single')
    setSelectedService(serviceId)
    router.push('/booking/date-time')
  }

  const handleServiceSelectSubscription = (serviceId: number) => {
    setBookingType('subscription')
    setSelectedService(serviceId)
    router.push('/booking/subscription-options')
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <p className="text-muted-foreground">Loading services...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 sm:p-6 md:p-8">
        <div className="max-w-2xl mx-auto">
          <div className="p-4 bg-destructive/10 text-destructive rounded-lg mb-4">
            {error}
          </div>
          <button
            onClick={() => router.push('/booking/postcode')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Change Postcode
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Select a Service</h1>
          <p className="text-muted-foreground">
            Services available in <span className="font-medium">{postcode}</span>
          </p>
        </div>

        {services.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">
              No services available in this area.
            </p>
            <button
              onClick={() => router.push('/booking/postcode')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Try a Different Postcode
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <button
                key={service.id}
                onClick={() => handleServiceClick(service.id)}
                className="p-6 text-left border border-border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer"
              >
                <div className="mb-2">
                  {service.category_name && (
                    <span className="text-xs text-muted-foreground uppercase tracking-wide">
                      {service.category_name}
                    </span>
                  )}
                </div>
                <h3 className="text-xl font-semibold mb-2">{service.name}</h3>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                  <span className="text-2xl font-bold">
                    {formatCurrency(typeof service.price === 'string' ? parseFloat(service.price) : service.price)}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {service.duration} min
                  </span>
                </div>
                {service.available_staff_count !== undefined && (
                  <div className="mt-2 text-xs text-muted-foreground">
                    {service.available_staff_count} {service.available_staff_count === 1 ? 'staff' : 'staff'} available in your area
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Service Detail Modal */}
      <ServiceDetailModal
        serviceId={selectedServiceId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelect={handleServiceSelect}
        onSelectSubscription={handleServiceSelectSubscription}
      />
    </div>
  )
}
