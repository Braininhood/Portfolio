'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CustomerBookingsHistory } from '@/components/customer/CustomerBookingsHistory'
import { CustomerPaymentsHistory } from '@/components/customer/CustomerPaymentsHistory'
import { CustomerNotesTags } from '@/components/customer/CustomerNotesTags'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Customer, CustomerDetailResponse, CustomerUpdateRequest } from '@/types/customer'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'

/**
 * Admin Customer Detail/Edit Page
 * Route: /ad/customers/[id] (Security: /ad/)
 */
export default function AdminCustomerDetail() {
  const router = useRouter()
  const params = useParams()
  const customerId = params.id as string

  const [customer, setCustomer] = useState<Customer | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'info' | 'bookings' | 'payments' | 'notes'>('info')

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address_line1: '',
    address_line2: '',
    city: '',
    postcode: '',
    country: 'United Kingdom',
  })

  useEffect(() => {
    if (customerId === 'new') {
      // New customer - initialize empty form
      setFormData({
        name: '',
        email: '',
        phone: '',
        address_line1: '',
        address_line2: '',
        city: '',
        postcode: '',
        country: 'United Kingdom',
      })
      setLoading(false)
    } else {
      fetchCustomer()
    }
  }, [customerId])

  const fetchCustomer = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<CustomerDetailResponse>(
        ADMIN_ENDPOINTS.CUSTOMERS.DETAIL(parseInt(customerId))
      )
      
      if (response.data.success && response.data.data) {
        const customerData = response.data.data
        setCustomer(customerData)
        setFormData({
          name: customerData.name,
          email: customerData.email,
          phone: customerData.phone || '',
          address_line1: customerData.address_line1 || '',
          address_line2: customerData.address_line2 || '',
          city: customerData.city || '',
          postcode: customerData.postcode || '',
          country: customerData.country || 'United Kingdom',
        })
      } else {
        setError('Failed to load customer')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load customer')
      console.error('Error fetching customer:', err)
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
      
      if (customerId === 'new') {
        // Create new customer
        const response = await apiClient.post(ADMIN_ENDPOINTS.CUSTOMERS.CREATE, formData)
        if (response.data.success) {
          router.push(`/ad/customers/${response.data.data.id}`)
        } else {
          setError('Failed to create customer')
        }
      } else {
        // Update existing customer
        const updateData: CustomerUpdateRequest = formData
        const response = await apiClient.patch(
          ADMIN_ENDPOINTS.CUSTOMERS.UPDATE(parseInt(customerId)),
          updateData
        )
        if (response.data.success) {
          setCustomer(response.data.data)
          setError(null)
        } else {
          setError('Failed to update customer')
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save customer')
      console.error('Error saving customer:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this customer? This action cannot be undone.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.CUSTOMERS.DELETE(parseInt(customerId)))
      router.push('/ad/customers')
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete customer')
      console.error('Error deleting customer:', err)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="admin">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading customer...</p>
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
                {customerId === 'new' ? 'New Customer' : customer?.name || 'Customer'}
              </h1>
              <p className="text-muted-foreground">
                {customerId === 'new' ? 'Create a new customer' : 'View and manage customer details'}
              </p>
            </div>
            {customerId !== 'new' && customer && (
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => router.push('/ad/customers')}>
                  Back to List
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  Delete Customer
                </Button>
              </div>
            )}
          </div>

          {/* Tabs */}
          {customerId !== 'new' && customer && (
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
                  onClick={() => setActiveTab('bookings')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'bookings'
                      ? 'border-b-2 border-primary text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Bookings
                </button>
                <button
                  onClick={() => setActiveTab('payments')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'payments'
                      ? 'border-b-2 border-primary text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Payments
                </button>
                <button
                  onClick={() => setActiveTab('notes')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'notes'
                      ? 'border-b-2 border-primary text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Notes & Tags
                </button>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-md">
              {error}
            </div>
          )}

          {/* Info Tab */}
          {(activeTab === 'info' || customerId === 'new') && (
            <form onSubmit={handleSave} className="space-y-6">
              <div className="border rounded-lg p-6 space-y-4">
                <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Name *</label>
                    <Input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
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
                      placeholder="e.g., +44 20 1234 5678"
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Postcode</label>
                    <Input
                      type="text"
                      value={formData.postcode}
                      onChange={(e) => setFormData(prev => ({ ...prev, postcode: e.target.value }))}
                      placeholder="e.g., SW1A 1AA"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Address Line 1</label>
                  <input
                    type="text"
                    value={formData.address_line1}
                    onChange={(e) => setFormData(prev => ({ ...prev, address_line1: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Address Line 2</label>
                  <input
                    type="text"
                    value={formData.address_line2}
                    onChange={(e) => setFormData(prev => ({ ...prev, address_line2: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">City</label>
                    <input
                      type="text"
                      value={formData.city}
                      onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Country</label>
                    <input
                      type="text"
                      value={formData.country}
                      onChange={(e) => setFormData(prev => ({ ...prev, country: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                </div>

                {customer && (
                  <div className="pt-4 border-t">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Account Status:</span>
                        <span className="ml-2">
                          {customer.user ? (
                            <span className="text-green-600">✓ Has Account</span>
                          ) : (
                            <span className="text-muted-foreground">Guest Customer</span>
                          )}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Created:</span>
                        <span className="ml-2">
                          {customer.created_at ? new Date(customer.created_at).toLocaleDateString() : '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Saving...' : customerId === 'new' ? 'Create Customer' : 'Save Changes'}
                  </Button>
                  {customerId !== 'new' && (
                    <Button type="button" variant="outline" onClick={() => router.push('/ad/customers')}>
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            </form>
          )}

          {/* Bookings Tab */}
          {activeTab === 'bookings' && customer && (
            <CustomerBookingsHistory customerId={customer.id!} />
          )}

          {/* Payments Tab */}
          {activeTab === 'payments' && customer && (
            <CustomerPaymentsHistory customerId={customer.id!} />
          )}

          {/* Notes & Tags Tab */}
          {activeTab === 'notes' && customer && (
            <CustomerNotesTags
              customer={customer}
              onUpdate={(updatedCustomer) => {
                setCustomer(updatedCustomer)
                fetchCustomer() // Refresh to get latest data
              }}
            />
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
