'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { DragDropOrder } from '@/components/service/DragDropOrder'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Service, ServiceListResponse, Category, CategoryListResponse, ReorderResponse } from '@/types/service'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
/**
 * Admin Service List Page
 * Route: /ad/services (Security: /ad/)
 */
export default function AdminServiceList() {
  const router = useRouter()
  const [services, setServices] = useState<Service[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [filterActive, setFilterActive] = useState<string>('all')
  const [searchName, setSearchName] = useState('')
  const [showReorder, setShowReorder] = useState(false)

  useEffect(() => {
    fetchCategories()
    fetchServices()
  }, [selectedCategory, filterActive, searchName])

  const fetchCategories = async () => {
    try {
      const response = await apiClient.get<CategoryListResponse>(ADMIN_ENDPOINTS.CATEGORIES.LIST)
      if (response.data.success && response.data.data) {
        setCategories(response.data.data)
      }
    } catch (err: any) {
      console.error('Error fetching categories:', err)
    }
  }

  const fetchServices = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory)
      }
      if (filterActive !== 'all') {
        params.append('is_active', filterActive)
      }
      
      const url = `${ADMIN_ENDPOINTS.SERVICES.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<ServiceListResponse>(url)
      
      if (response.data.success && response.data.data) {
        let filteredServices = response.data.data
        
        // Client-side name search
        if (searchName) {
          filteredServices = filteredServices.filter(service =>
            service.name.toLowerCase().includes(searchName.toLowerCase())
          )
        }
        
        setServices(filteredServices)
      } else {
        setError('Failed to load services')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load services')
      console.error('Error fetching services:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this service?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.SERVICES.DELETE(id))
      fetchServices() // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete service')
      console.error('Error deleting service:', err)
    }
  }

  const formatCurrency = (price: string | number, currency: string = 'GBP') => {
    const amount = typeof price === 'string' ? parseFloat(price) : price
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes}m`
    }
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Service Management</h1>
              <p className="text-muted-foreground">
                Manage services, categories, pricing, and staff assignments
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowReorder(!showReorder)}>
                {showReorder ? 'Hide Reorder' : 'Reorder Services'}
              </Button>
              <Button variant="outline" onClick={() => router.push('/ad/services/categories')}>
                Manage Categories
              </Button>
              <Button onClick={() => router.push('/ad/services/new')}>
                Add New Service
              </Button>
            </div>
          </div>

          {/* Drag and Drop Reorder */}
          {showReorder && (
            <div className="bg-card border rounded-lg p-6 mb-6">
              <DragDropOrder
                items={services.map(s => ({ id: s.id!, name: s.name, position: s.position }))}
                onReorder={async (reorderedItems) => {
                  const response = await apiClient.post<ReorderResponse>(
                    ADMIN_ENDPOINTS.SERVICES.REORDER,
                    { services: reorderedItems }
                  )
                  if (response.data.success) {
                    fetchServices()
                    setShowReorder(false)
                  }
                }}
                itemType="service"
              />
            </div>
          )}

          {/* Filters */}
          <div className="bg-card border rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  <option value="all">All Categories</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Status</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                >
                  <option value="all">All</option>
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Search</label>
                <input
                  type="text"
                  placeholder="Search by name..."
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading services...</p>
            </div>
          )}

          {/* Service List */}
          {!loading && !error && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {services.length} service{services.length !== 1 ? 's' : ''}
              </div>
              <div className="bg-card border rounded-lg overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Position</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {services.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center text-muted-foreground">
                          No services found
                        </td>
                      </tr>
                    ) : (
                      services.map((service) => (
                        <tr key={service.id} className="hover:bg-muted/50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="text-muted-foreground">#{service.position}</span>
                          </td>
                          <td className="px-6 py-4">
                            <Link href={`/ad/services/${service.id}`} className="font-medium hover:underline">
                              {service.name}
                            </Link>
                            {service.description && (
                              <div className="text-sm text-muted-foreground mt-1 line-clamp-1">
                                {service.description}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                              {service.category_name || service.category?.name}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {formatCurrency(service.price, service.currency)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {formatDuration(service.duration)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {service.is_active ? (
                              <span className="text-green-600">✓ Active</span>
                            ) : (
                              <span className="text-muted-foreground">Inactive</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => router.push(`/ad/services/${service.id}`)}
                              >
                                Edit
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDelete(service.id!)}
                              >
                                Delete
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
