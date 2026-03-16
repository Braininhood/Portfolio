'use client'

import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { Customer, CustomerUpdateRequest } from '@/types/customer'
import { useState } from 'react'

interface CustomerNotesTagsProps {
  customer: Customer
  onUpdate: (updatedCustomer: Customer) => void
}

export function CustomerNotesTags({ customer, onUpdate }: CustomerNotesTagsProps) {
  const [notes, setNotes] = useState(customer.notes || '')
  const [tags, setTags] = useState<string[]>(customer.tags || [])
  const [newTag, setNewTag] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSaveNotes = async () => {
    try {
      setSaving(true)
      setError(null)
      
      const updateData: CustomerUpdateRequest = {
        notes: notes,
      }
      
      const response = await apiClient.patch(
        ADMIN_ENDPOINTS.CUSTOMERS.UPDATE(customer.id!),
        updateData
      )
      
      if (response.data.success) {
        onUpdate(response.data.data)
      } else {
        setError('Failed to save notes')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save notes')
      console.error('Error saving notes:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleAddTag = async () => {
    if (!newTag.trim()) return
    
    const tagToAdd = newTag.trim().toLowerCase()
    if (tags.includes(tagToAdd)) {
      setNewTag('')
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const updatedTags = [...tags, tagToAdd]
      const updateData: CustomerUpdateRequest = {
        tags: updatedTags,
      }
      
      const response = await apiClient.patch(
        ADMIN_ENDPOINTS.CUSTOMERS.UPDATE(customer.id!),
        updateData
      )
      
      if (response.data.success) {
        setTags(updatedTags)
        setNewTag('')
        onUpdate(response.data.data)
      } else {
        setError('Failed to add tag')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to add tag')
      console.error('Error adding tag:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleRemoveTag = async (tagToRemove: string) => {
    try {
      setSaving(true)
      setError(null)
      
      const updatedTags = tags.filter(tag => tag !== tagToRemove)
      const updateData: CustomerUpdateRequest = {
        tags: updatedTags,
      }
      
      const response = await apiClient.patch(
        ADMIN_ENDPOINTS.CUSTOMERS.UPDATE(customer.id!),
        updateData
      )
      
      if (response.data.success) {
        setTags(updatedTags)
        onUpdate(response.data.data)
      } else {
        setError('Failed to remove tag')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to remove tag')
      console.error('Error removing tag:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Notes Section */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Notes</h3>
        <div className="bg-card border rounded-lg p-4">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add internal notes about this customer..."
            rows={6}
            className="w-full px-3 py-2 border rounded-md mb-4"
          />
          <Button onClick={handleSaveNotes} disabled={saving}>
            {saving ? 'Saving...' : 'Save Notes'}
          </Button>
        </div>
      </div>

      {/* Tags Section */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Tags</h3>
        <div className="bg-card border rounded-lg p-4">
          {/* Existing Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm flex items-center gap-2"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="text-primary hover:text-primary/70"
                    type="button"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Add Tag */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleAddTag()
                }
              }}
              placeholder="Add a tag (e.g., vip, repeat, etc.)"
              className="flex-1 px-3 py-2 border rounded-md"
            />
            <Button onClick={handleAddTag} disabled={saving || !newTag.trim()}>
              Add Tag
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Common tags: vip, repeat, new, problem, preferred
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg">
          {error}
        </div>
      )}
    </div>
  )
}
