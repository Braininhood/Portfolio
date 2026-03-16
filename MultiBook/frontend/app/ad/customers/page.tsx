'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Customer, CustomerListResponse } from '@/types/customer'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

/**
 * Admin Customer List Page
 * Route: /ad/customers (Security: /ad/)
 */
export default function AdminCustomerList() {
  const router = useRouter()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Search and filters
  const [searchName, setSearchName] = useState('')
  const [searchEmail, setSearchEmail] = useState('')
  const [searchPostcode, setSearchPostcode] = useState('')
  const [searchPhone, setSearchPhone] = useState('')
  const [filterHasAccount, setFilterHasAccount] = useState<string>('all')
  const [filterTags, setFilterTags] = useState('')

  useEffect(() => {
    fetchCustomers()
  }, [searchName, searchEmail, searchPostcode, searchPhone, filterHasAccount, filterTags])

  const fetchCustomers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams()
      if (searchName) params.append('name', searchName)
      if (searchEmail) params.append('email', searchEmail)
      if (searchPostcode) params.append('postcode', searchPostcode)
      if (searchPhone) params.append('phone', searchPhone)
      if (filterHasAccount !== 'all') params.append('has_user_account', filterHasAccount)
      if (filterTags) params.append('tags', filterTags)
      
      const url = `${ADMIN_ENDPOINTS.CUSTOMERS.LIST}${params.toString() ? '?' + params.toString() : ''}`
      const response = await apiClient.get<CustomerListResponse>(url)
      
      if (response.data.success && response.data.data) {
        setCustomers(response.data.data)
      } else {
        setError('Failed to load customers')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load customers')
      console.error('Error fetching customers:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this customer?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.CUSTOMERS.DELETE(id))
      fetchCustomers() // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete customer')
      console.error('Error deleting customer:', err)
    }
  }

  const clearFilters = () => {
    setSearchName('')
    setSearchEmail('')
    setSearchPostcode('')
    setSearchPhone('')
    setFilterHasAccount('all')
    setFilterTags('')
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Customer Management</h1>
              <p className="text-muted-foreground">
                Manage customers, view booking history, and track payments
              </p>
            </div>
            <Button onClick={() => router.push('/ad/customers/new')}>
              Add New Customer
            </Button>
          </div>

          {/* Search and Filters */}
          <div className="bg-card border rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Search & Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Name</label>
                <input
                  type="text"
                  placeholder="Search by name..."
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="text"
                  placeholder="Search by email..."
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Postcode</label>
                <input
                  type="text"
                  placeholder="Search by postcode..."
                  value={searchPostcode}
                  onChange={(e) => setSearchPostcode(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Phone</label>
                <input
                  type="text"
                  placeholder="Search by phone..."
                  value={searchPhone}
                  onChange={(e) => setSearchPhone(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Has Account</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={filterHasAccount}
                  onChange={(e) => setFilterHasAccount(e.target.value)}
                >
                  <option value="all">All</option>
                  <option value="true">With Account</option>
                  <option value="false">Guest Only</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Tags</label>
                <input
                  type="text"
                  placeholder="Filter by tag..."
                  value={filterTags}
                  onChange={(e) => setFilterTags(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>
            <div className="mt-4">
              <Button variant="outline" onClick={clearFilters}>
                Clear Filters
              </Button>
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
              <p className="text-muted-foreground">Loading customers...</p>
            </div>
          )}

          {/* Customer List */}
          {!loading && !error && (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                Showing {customers.length} customer{customers.length !== 1 ? 's' : ''}
              </div>
              <div className="bg-card border rounded-lg overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Phone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Postcode</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Account</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Tags</th>
                      <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {customers.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-8 text-center text-muted-foreground">
                          No customers found
                        </td>
                      </tr>
                    ) : (
                      customers.map((customer) => (
                        <tr key={customer.id} className="hover:bg-muted/50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Link href={`/ad/customers/${customer.id}`} className="font-medium hover:underline">
                              {customer.name}
                            </Link>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">{customer.email}</td>
                          <td className="px-6 py-4 whitespace-nowrap">{customer.phone || '-'}</td>
                          <td className="px-6 py-4 whitespace-nowrap">{customer.postcode || '-'}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {customer.user ? (
                              <span className="text-green-600">✓ Account</span>
                            ) : (
                              <span className="text-muted-foreground">Guest</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {customer.tags && customer.tags.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {customer.tags.slice(0, 2).map((tag, idx) => (
                                  <span key={idx} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                                    {tag}
                                  </span>
                                ))}
                                {customer.tags.length > 2 && (
                                  <span className="px-2 py-1 text-xs text-muted-foreground">
                                    +{customer.tags.length - 2}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => router.push(`/ad/customers/${customer.id}`)}
                              >
                                View
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDelete(customer.id!)}
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
