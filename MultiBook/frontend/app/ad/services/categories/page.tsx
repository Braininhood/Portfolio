'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { Button } from '@/components/ui/button'
import { DragDropOrder } from '@/components/service/DragDropOrder'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Category, CategoryListResponse, ReorderResponse } from '@/types/service'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

/**
 * Admin Category Management Page
 * Route: /ad/services/categories (Security: /ad/)
 */
export default function AdminCategoryManagement() {
  const router = useRouter()
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    position: 0,
    is_active: true,
  })
  const [showReorder, setShowReorder] = useState(false)

  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.get<CategoryListResponse>(ADMIN_ENDPOINTS.CATEGORIES.LIST)
      
      if (response.data.success && response.data.data) {
        setCategories(response.data.data)
      } else {
        setError('Failed to load categories')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load categories')
      console.error('Error fetching categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim()) {
      setError('Name is required')
      return
    }

    try {
      if (editingId) {
        // Update existing
        await apiClient.patch(ADMIN_ENDPOINTS.CATEGORIES.UPDATE(editingId), formData)
      } else {
        // Create new
        await apiClient.post(ADMIN_ENDPOINTS.CATEGORIES.CREATE, formData)
      }
      
      setEditingId(null)
      setFormData({ name: '', description: '', position: 0, is_active: true })
      fetchCategories()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save category')
      console.error('Error saving category:', err)
    }
  }

  const handleEdit = (category: Category) => {
    setEditingId(category.id!)
    setFormData({
      name: category.name,
      description: category.description || '',
      position: category.position,
      is_active: category.is_active,
    })
  }

  const handleCancel = () => {
    setEditingId(null)
    setFormData({ name: '', description: '', position: 0, is_active: true })
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category? Services in this category will need to be reassigned.')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.CATEGORIES.DELETE(id))
      fetchCategories()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete category')
      console.error('Error deleting category:', err)
    }
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold mb-2">Category Management</h1>
              <p className="text-muted-foreground">
                Organize services into categories
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowReorder(!showReorder)}>
                {showReorder ? 'Hide Reorder' : 'Reorder Categories'}
              </Button>
              <Button variant="outline" onClick={() => router.push('/ad/services')}>
                Back to Services
              </Button>
            </div>
          </div>

          {/* Drag and Drop Reorder */}
          {showReorder && (
            <div className="bg-card border rounded-lg p-6 mb-6">
              <DragDropOrder
                items={categories.map(c => ({ id: c.id!, name: c.name, position: c.position }))}
                onReorder={async (reorderedItems) => {
                  const response = await apiClient.post<ReorderResponse>(
                    ADMIN_ENDPOINTS.CATEGORIES.REORDER,
                    { categories: reorderedItems }
                  )
                  if (response.data.success) {
                    fetchCategories()
                    setShowReorder(false)
                  }
                }}
                itemType="category"
              />
            </div>
          )}

          {/* Create/Edit Form */}
          <div className="bg-card border rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">
              {editingId ? 'Edit Category' : 'Create New Category'}
            </h2>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={3}
                  placeholder="Category description..."
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="w-4 h-4"
                />
                <label className="text-sm font-medium">Category is active</label>
              </div>
              <div className="flex gap-2">
                <Button type="submit">
                  {editingId ? 'Update Category' : 'Create Category'}
                </Button>
                {editingId && (
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Categories List */}
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading categories...</p>
            </div>
          ) : (
            <div className="bg-card border rounded-lg overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase">Position</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase">Services</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {categories.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                        No categories found
                      </td>
                    </tr>
                  ) : (
                    categories.map((category) => (
                      <tr key={category.id} className="hover:bg-muted/50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-muted-foreground">#{category.position}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="font-medium">{category.name}</div>
                          {category.description && (
                            <div className="text-sm text-muted-foreground mt-1">
                              {category.description}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {category.services_count || 0} service{category.services_count !== 1 ? 's' : ''}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {category.is_active ? (
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
                              onClick={() => handleEdit(category)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(category.id!)}
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
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
