'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import type { Customer, CustomerDetailResponse, CustomerUpdateRequest } from '@/types/customer'
import { useEffect, useState } from 'react'

/**
 * Customer Profile Page
 * Route: /cus/profile (Security: /cus/)
 */
export default function CustomerProfile() {
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

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
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<CustomerDetailResponse>(
        CUSTOMER_ENDPOINTS.PROFILE.GET
      )
      
      if (response.data.success && response.data.data) {
        const raw = response.data.data
        const customerData = Array.isArray(raw) ? raw[0] : raw
        if (!customerData) {
          setError('Profile not found')
          return
        }
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
        setError('Failed to load profile')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load profile')
      console.error('Error fetching profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (!formData.name.trim() || !formData.email.trim()) {
      setError('Name and email are required')
      return
    }

    if (!customer?.id) {
      setError('Profile not loaded')
      return
    }

    try {
      setSaving(true)
      
      const updateData: CustomerUpdateRequest = formData
      const response = await apiClient.patch(
        CUSTOMER_ENDPOINTS.PROFILE.UPDATE(customer.id),
        updateData
      )
      
      if (response.data.success) {
        setCustomer(response.data.data)
        setSuccess(true)
        setTimeout(() => setSuccess(false), 3000)
      } else {
        setError('Failed to update profile')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to update profile')
      console.error('Error updating profile:', err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <ProtectedRoute requiredRole="customer">
        <DashboardLayout>
          <div className="container mx-auto p-4 sm:p-6 md:p-8">
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading profile...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requiredRole="customer">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">My Profile</h1>
            <p className="text-muted-foreground">
              Manage your account information and preferences
            </p>
          </div>

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 text-green-800 p-4 rounded-lg mb-6">
              Profile updated successfully!
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-6">
            <div className="bg-card border rounded-lg p-6 space-y-4">
              <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Email *</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                    inputMode="email"
                    autoComplete="email"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Phone</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                    inputMode="tel"
                    autoComplete="tel"
                    placeholder="e.g., +44 20 1234 5678"
                  />
                </div>
              </div>
            </div>

            <div className="bg-card border rounded-lg p-6 space-y-4">
              <h2 className="text-xl font-semibold mb-4">Address</h2>
              
              <div>
                <label className="block text-sm font-medium mb-2">Address Line 1</label>
                <input
                  type="text"
                  value={formData.address_line1}
                  onChange={(e) => setFormData(prev => ({ ...prev, address_line1: e.target.value }))}
                  className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                  autoComplete="address-line1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Address Line 2</label>
                <input
                  type="text"
                  value={formData.address_line2}
                  onChange={(e) => setFormData(prev => ({ ...prev, address_line2: e.target.value }))}
                  className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                  autoComplete="address-line2"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">City</label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                    className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                    autoComplete="address-level2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Postcode</label>
                  <input
                    type="text"
                    value={formData.postcode}
                    onChange={(e) => setFormData(prev => ({ ...prev, postcode: e.target.value }))}
                    className="w-full px-4 py-3 border rounded-md min-h-[44px] text-base"
                    autoComplete="postal-code"
                    placeholder="e.g., SW1A 1AA"
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
            </div>

            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
