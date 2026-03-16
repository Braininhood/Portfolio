'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import type { StaffArea, StaffAreaCreateRequest } from '@/types/staff'
import { validateUKPostcode } from '@/lib/utils'
import { ServiceAreaMap } from './ServiceAreaMap'

interface StaffAreaManagerProps {
  staffId: number
  areas: StaffArea[]
  onUpdate: () => void
}

interface AddressSuggestion {
  place_id: string
  description: string
  structured_formatting?: {
    main_text: string
    secondary_text: string
  }
}

export function StaffAreaManager({ staffId, areas, onUpdate }: StaffAreaManagerProps) {
  const [localAreas, setLocalAreas] = useState<StaffArea[]>(areas)
  const [editingArea, setEditingArea] = useState<StaffArea | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    postcode: '',
    radius_miles: 10,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AddressSuggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const autocompleteRef = useRef<HTMLDivElement>(null)
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    setLocalAreas(areas)
  }, [areas])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleAutocompleteSearch = async (query: string) => {
    if (query.length < 3) {
      setAutocompleteSuggestions([])
      setShowSuggestions(false)
      return
    }

    try {
      const response = await apiClient.get('/addr/autocomplete/', {
        params: { query },
      })

      if (response.data.success && response.data.data) {
        setAutocompleteSuggestions(response.data.data.predictions || [])
        setShowSuggestions(true)
      }
    } catch (err) {
      console.error('Autocomplete error:', err)
    }
  }

  const handlePostcodeChange = (value: string) => {
    setFormData(prev => ({ ...prev, postcode: value }))
    
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current)
    }

    if (value.length >= 3) {
      autocompleteTimeoutRef.current = setTimeout(() => {
        handleAutocompleteSearch(value)
      }, 300)
    } else {
      setAutocompleteSuggestions([])
      setShowSuggestions(false)
    }
  }

  const handleAddressSelect = async (suggestion: AddressSuggestion) => {
    try {
      const response = await apiClient.get('/addr/validate/', {
        params: { place_id: suggestion.place_id },
      })

      if (response.data.success && response.data.data) {
        const addressData = response.data.data
        if (addressData.postcode) {
          setFormData(prev => ({ ...prev, postcode: addressData.postcode }))
        }
      }
    } catch (err) {
      console.error('Address validation error:', err)
    }

    setShowSuggestions(false)
    setAutocompleteSuggestions([])
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.postcode.trim()) {
      setError('Postcode is required')
      return
    }

    if (!validateUKPostcode(formData.postcode)) {
      setError('Please enter a valid UK postcode')
      return
    }

    if (formData.radius_miles <= 0 || formData.radius_miles > 60) {
      setError('Radius must be between 0 and 60 miles')
      return
    }

    try {
      setLoading(true)
      
      if (editingArea?.id) {
        // Update existing area
        await apiClient.patch(
          ADMIN_ENDPOINTS.STAFF.AREAS.UPDATE(editingArea.id),
          {
            staff: staffId,
            postcode: formData.postcode,
            radius_miles: formData.radius_miles,
            is_active: formData.is_active,
          }
        )
      } else {
        // Create new area
        const request: StaffAreaCreateRequest = {
          staff: staffId,
          postcode: formData.postcode,
          radius_miles: formData.radius_miles,
          is_active: formData.is_active,
        }
        await apiClient.post(ADMIN_ENDPOINTS.STAFF.AREAS.CREATE, request)
      }

      setFormData({ postcode: '', radius_miles: 10, is_active: true })
      setShowForm(false)
      setEditingArea(null)
      onUpdate()
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to save service area')
      console.error('Error saving area:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (area: StaffArea) => {
    setEditingArea(area)
    setFormData({
      postcode: area.postcode,
      radius_miles: area.radius_miles,
      is_active: area.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this service area?')) {
      return
    }

    try {
      await apiClient.delete(ADMIN_ENDPOINTS.STAFF.AREAS.DELETE(id))
      onUpdate()
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete area')
      console.error('Error deleting area:', err)
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingArea(null)
    setFormData({ postcode: '', radius_miles: 10, is_active: true })
    setError(null)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Service Areas</h3>
          <p className="text-sm text-muted-foreground">
            Define postcode areas where this staff member can provide services
          </p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)} size="sm">
            Add Area
          </Button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="border rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Postcode (Center)</label>
            <div className="relative" ref={autocompleteRef}>
              <input
                type="text"
                value={formData.postcode}
                onChange={(e) => handlePostcodeChange(e.target.value)}
                placeholder="e.g., SW1A 1AA"
                className="w-full px-3 py-2 border rounded-md"
                required
              />
              {showSuggestions && autocompleteSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto">
                  {autocompleteSuggestions.map((suggestion) => (
                    <button
                      key={suggestion.place_id}
                      type="button"
                      onClick={() => handleAddressSelect(suggestion)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100"
                    >
                      <div className="font-medium">
                        {suggestion.structured_formatting?.main_text || suggestion.description}
                      </div>
                      {suggestion.structured_formatting?.secondary_text && (
                        <div className="text-sm text-muted-foreground">
                          {suggestion.structured_formatting.secondary_text}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Service Radius: {formData.radius_miles} miles
            </label>
            <input
              type="range"
              min="1"
              max="60"
              step="1"
              value={formData.radius_miles}
              onChange={(e) => setFormData(prev => ({ ...prev, radius_miles: parseFloat(e.target.value) }))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>1 mile</span>
              <span>60 miles</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active_area"
              checked={formData.is_active}
              onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="is_active_area" className="text-sm">
              Active
            </label>
          </div>

          {error && (
            <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading} size="sm">
              {editingArea ? 'Update' : 'Add'} Area
            </Button>
            <Button type="button" variant="outline" onClick={handleCancel} size="sm">
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Areas List */}
      <div className="space-y-2">
        {localAreas.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No service areas defined. Add one to get started.
          </p>
        ) : (
          localAreas.map((area) => (
            <div
              key={area.id}
              data-area-id={area.id}
              className="flex items-center justify-between border rounded-lg p-3"
            >
              <div>
                <div className="font-medium">{area.postcode}</div>
                <div className="text-sm text-muted-foreground">
                  Radius: {area.radius_miles} miles
                  {!area.is_active && <span className="ml-2 text-destructive">(Inactive)</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(area)}
                >
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => area.id && handleDelete(area.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Map Visualization */}
      {localAreas.length > 0 && (
        <div className="mt-6">
          <h4 className="text-md font-semibold mb-3">Service Area Coverage Map</h4>
          <div className="border rounded-lg overflow-hidden min-h-[280px] h-[50vh] max-h-[500px]">
            <ServiceAreaMap
              areas={localAreas}
              onAreaClick={(area) => {
                // Scroll to area in list or highlight it
                const areaElement = document.querySelector(`[data-area-id="${area.id}"]`)
                if (areaElement) {
                  areaElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                }
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Map shows service area coverage circles. Click on an area to view details.
          </p>
        </div>
      )}
    </div>
  )
}
