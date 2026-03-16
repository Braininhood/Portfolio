'use client'

/**
 * Booking Step 5: Guest Details & Payment
 * Route: /booking/details (Public - Guest Checkout)
 *
 * When user is logged in (customer), details are pre-filled from profile.
 * NO LOGIN REQUIRED for guest checkout.
 */
import { useBookingStore } from '@/store/booking-store'
import { useRouter } from 'next/navigation'
import { useEffect, useState, useRef } from 'react'
import { apiClient } from '@/lib/api/client'
import { PUBLIC_ENDPOINTS } from '@/lib/api/endpoints'
import { CUSTOMER_ENDPOINTS } from '@/lib/api/endpoints'
import { useAuthContext } from '@/components/auth/AuthProvider'
import { validateUKPostcode, normalizeUKPostcode } from '@/lib/utils'
import type { AddressData } from '@/types/api'

interface AddressSuggestion {
  place_id: string
  description: string
  structured_formatting?: {
    main_text: string
    secondary_text: string
  }
}

export default function GuestDetailsPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuthContext()
  const {
    postcode,
    selectedService,
    selectedDate,
    selectedTime,
    selectedStaff: _selectedStaff,
    setPostcode: setStorePostcode,
    setGuestDetails,
    setNotes,
    setCustomerId,
    guestName,
    guestEmail,
    guestPhone,
    address,
    notes,
  } = useBookingStore()

  const [formData, setFormData] = useState({
    name: guestName || '',
    email: guestEmail || '',
    phone: guestPhone || '',
    address_line1: address?.line1 || '',
    address_line2: address?.line2 || '',
    city: address?.city || '',
    postcode: address?.postcode || postcode || '',
    country: address?.country || 'United Kingdom',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AddressSuggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [autocompleteQuery, setAutocompleteQuery] = useState('')
  const autocompleteRef = useRef<HTMLDivElement>(null)
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout>()
  /** When user changes postcode: true if selected service is not available for that postcode */
  const [postcodeServiceUnavailable, setPostcodeServiceUnavailable] = useState(false)
  const [postcodeCheckLoading, setPostcodeCheckLoading] = useState(false)
  const postcodeCheckTimeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    // Redirect if required booking data is missing
    if (!postcode) {
      router.push('/booking/postcode')
      return
    }
    if (!selectedService) {
      router.push('/booking/services')
      return
    }
    if (!selectedDate || !selectedTime) {
      router.push('/booking/date-time')
      return
    }

    // Auto-fill postcode if available
    if (postcode && !formData.postcode) {
      setFormData(prev => ({ ...prev, postcode }))
    }
  }, [postcode, selectedService, selectedDate, selectedTime, router])

  // Pre-fill from logged-in customer profile (so /booking/details shows all user info)
  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'customer') return
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (!token) return

    const fetchAndPreFill = async () => {
      try {
        const response = await apiClient.get(CUSTOMER_ENDPOINTS.PROFILE.GET)
        if (!response.data?.success || !response.data?.data) return
        const data = response.data.data
        const profile = Array.isArray(data) ? data[0] : data
        if (!profile?.id || !profile?.email) return

        setFormData(prev => ({
          ...prev,
          name: profile.name || prev.name,
          email: profile.email || prev.email,
          phone: profile.phone || prev.phone,
          address_line1: profile.address_line1 || prev.address_line1,
          address_line2: profile.address_line2 || prev.address_line2,
          city: profile.city || prev.city,
          postcode: profile.postcode || postcode || prev.postcode,
          country: profile.country || 'United Kingdom',
        }))
        const addr: AddressData = {
          line1: profile.address_line1 || '',
          line2: profile.address_line2 || '',
          city: profile.city || '',
          postcode: profile.postcode || postcode || '',
          country: profile.country || 'United Kingdom',
        }
        setGuestDetails(
          profile.email || '',
          profile.name || '',
          profile.phone || '',
          addr
        )
        setCustomerId(profile.id)
      } catch {
        // Not logged in or profile fetch failed – keep form empty
      }
    }

    fetchAndPreFill()
  }, [isAuthenticated, user?.role, postcode, setGuestDetails, setCustomerId])

  // Auto-fill address from postcode (if address fields are empty)
  useEffect(() => {
    if (postcode && formData.postcode === postcode) {
      // Auto-fill when postcode is available and address fields are empty
      if (!formData.address_line1 || !formData.city) {
        autoFillFromPostcode(postcode)
      }
    }
  }, [postcode, formData.postcode])

  // Auto-trigger search when postcode is entered manually (debounced)
  useEffect(() => {
    if (formData.postcode && formData.postcode.length >= 5 && !formData.address_line1) {
      // If user types a postcode and address is empty, trigger autocomplete search
      const trimmedPostcode = formData.postcode.trim()
      if (trimmedPostcode !== autocompleteQuery && validateUKPostcode(trimmedPostcode)) {
        // Only trigger if postcode is valid UK format
        const timeoutId = setTimeout(() => {
          setAutocompleteQuery(trimmedPostcode)
          handleAutocompleteSearch(trimmedPostcode)
        }, 500) // Debounce to avoid too many API calls
        
        return () => clearTimeout(timeoutId)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.postcode])

  // Re-check if selected service is available when user enters a different postcode
  useEffect(() => {
    const pc = formData.postcode.trim().toUpperCase().replace(/\s+/g, ' ')
    const bookingPostcode = (postcode || '').trim().toUpperCase().replace(/\s+/g, ' ')
    if (!pc || pc.length < 5 || !validateUKPostcode(pc) || !selectedService) {
      setPostcodeServiceUnavailable(false)
      return
    }
    if (pc === bookingPostcode) {
      setPostcodeServiceUnavailable(false)
      return
    }
    if (postcodeCheckTimeoutRef.current) clearTimeout(postcodeCheckTimeoutRef.current)
    postcodeCheckTimeoutRef.current = setTimeout(async () => {
      setPostcodeCheckLoading(true)
      setPostcodeServiceUnavailable(false)
      try {
        const response = await apiClient.get(PUBLIC_ENDPOINTS.SERVICES.BY_POSTCODE, {
          params: { postcode: pc },
        })
        if (response.data?.success && Array.isArray(response.data.data)) {
          const serviceIds = response.data.data.map((s: { id: number }) => s.id)
          setPostcodeServiceUnavailable(!serviceIds.includes(selectedService))
        } else {
          setPostcodeServiceUnavailable(true)
        }
      } catch {
        setPostcodeServiceUnavailable(true)
      } finally {
        setPostcodeCheckLoading(false)
      }
    }, 600)
    return () => {
      if (postcodeCheckTimeoutRef.current) clearTimeout(postcodeCheckTimeoutRef.current)
    }
  }, [formData.postcode, selectedService, postcode])

  // Close autocomplete when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const autoFillFromPostcode = async (postcode: string) => {
    try {
      const response = await apiClient.post(PUBLIC_ENDPOINTS.ADDRESS.VALIDATE, {
        postcode,
      })

      if (response.data.success && response.data.data) {
        const addressData = response.data.data
        setFormData(prev => ({
          ...prev,
          address_line1: addressData.address_line1 || prev.address_line1,
          city: addressData.city || prev.city,
          postcode: addressData.postcode || postcode,
        }))
      }
    } catch (_error) {
      // Silently fail - user can fill manually
    }
  }

  const handleAutocompleteSearch = async (query: string) => {
    if (!query || query.trim().length < 2) {
      setAutocompleteSuggestions([])
      setShowSuggestions(false)
      return
    }

    const trimmedQuery = query.trim()

    // Debounce API calls
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current)
    }

    autocompleteTimeoutRef.current = setTimeout(async () => {
      try {
        console.log('🔍 Searching for:', trimmedQuery)
        const response = await apiClient.get(PUBLIC_ENDPOINTS.ADDRESS.AUTOCOMPLETE, {
          params: { query: trimmedQuery },
        })

        console.log('✅ API Response:', response.data)

        if (response.data.success && response.data.data) {
          const suggestions = response.data.data || []
          console.log('📋 Suggestions found:', suggestions.length, suggestions)
          setAutocompleteSuggestions(suggestions)
          setShowSuggestions(suggestions.length > 0)
        } else {
          // Check for API key error
          if (response.data.error?.code === 'API_KEY_MISSING') {
            console.error('❌ Google Maps API key not configured!')
            console.error('Please add GOOGLE_MAPS_API_KEY to backend/.env file')
          }
          console.warn('⚠️ No suggestions in response:', response.data)
          setAutocompleteSuggestions([])
          setShowSuggestions(false)
        }
      } catch (error: any) {
        // Log detailed error for debugging
        console.error('❌ Autocomplete error:', error)
        console.error('❌ Error response:', error.response?.data)
        console.error('❌ Error status:', error.response?.status)
        console.error('❌ Error message:', error.message)
        setAutocompleteSuggestions([])
        setShowSuggestions(false)
      }
    }, 300)
  }

  const handleAddressSelect = async (suggestion: AddressSuggestion) => {
    setShowSuggestions(false)
    // Keep the selected address in the search box for reference
    setAutocompleteQuery(suggestion.description)

    try {
      const response = await apiClient.post(PUBLIC_ENDPOINTS.ADDRESS.VALIDATE, {
        place_id: suggestion.place_id,
      })

      if (response.data.success && response.data.data) {
        const addressData = response.data.data
        // Auto-fill all address fields - user can edit manually if needed
        setFormData(prev => ({
          ...prev,
          address_line1: addressData.address_line1 || prev.address_line1,
          address_line2: addressData.address_line2 || prev.address_line2 || '',
          city: addressData.city || prev.city,
          postcode: addressData.postcode || prev.postcode,
          country: addressData.country || 'United Kingdom',
        }))
      }
    } catch (_error) {
      // If API fails, try to parse from description
      const parts = suggestion.description.split(',')
      if (parts.length > 0) {
        setFormData(prev => ({
          ...prev,
          address_line1: parts[0]?.trim() || prev.address_line1,
          city: parts[parts.length - 2]?.trim() || prev.city,
        }))
      }
    }
  }

  const validateForm = (): { valid: boolean; errors: Record<string, string> } => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required'
    } else if (!/^[\d\s\-\+\(\)]+$/.test(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number'
    }

    if (!formData.address_line1.trim()) {
      newErrors.address_line1 = 'Address line 1 is required'
    }

    if (!formData.city.trim()) {
      newErrors.city = 'City/town is required'
    }

    if (!formData.postcode.trim()) {
      newErrors.postcode = 'Postcode is required'
    } else if (!validateUKPostcode(formData.postcode)) {
      newErrors.postcode = 'Please enter a valid UK postcode (e.g. SW1A 2AD or M1 1AA)'
    }

    setErrors(newErrors)
    return { valid: Object.keys(newErrors).length === 0, errors: newErrors }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (postcodeServiceUnavailable) {
      setErrors({ submit: 'This service is not available for the postcode you entered. Please use an address we cover or choose a different service.' })
      return
    }

    const normalizedPostcode = normalizeUKPostcode(formData.postcode)

    const { valid, errors: validationErrors } = validateForm()
    if (!valid) {
      const firstErrorField = Object.keys(validationErrors)[0]
      if (firstErrorField) {
        setTimeout(() => {
          const element = document.getElementById(firstErrorField)
          element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
          element?.focus()
        }, 0)
      }
      return
    }

    if (!formData.name.trim() || !formData.email.trim() || !formData.phone.trim() ||
        !formData.address_line1.trim() || !formData.city.trim() || !formData.postcode.trim()) {
      setErrors({ submit: 'Please fill in all required fields before continuing.' })
      return
    }

    // Final check: ensure selected service is available for this postcode (handles manual or autofill)
    setLoading(true)
    setErrors({})
    try {
      const response = await apiClient.get(PUBLIC_ENDPOINTS.SERVICES.BY_POSTCODE, {
        params: { postcode: normalizedPostcode },
      })
      const serviceIds: number[] = response.data?.success && Array.isArray(response.data.data)
        ? response.data.data.map((s: { id: number }) => s.id)
        : []
      if (!serviceIds.includes(selectedService!)) {
        setErrors({
          submit: 'This service is not available for your address. Please use a postcode we cover or go back to choose a different service.',
          postcode: 'We don\'t cover this postcode for the selected service.',
        })
        setLoading(false)
        return
      }
    } catch {
      setErrors({
        submit: 'We couldn\'t check your address. Please try again or use a different postcode.',
      })
      setLoading(false)
      return
    }
    setLoading(false)

    const addressData: AddressData = {
      line1: formData.address_line1.trim(),
      line2: formData.address_line2.trim(),
      city: formData.city.trim(),
      postcode: normalizedPostcode,
      country: formData.country,
    }

    setGuestDetails(formData.email.trim(), formData.name.trim(), formData.phone.trim(), addressData)
    setStorePostcode(normalizedPostcode)
    if (notes) {
      setNotes(notes)
    }

    router.push('/booking/payment')
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 md:p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Your Details</h1>
          <p className="text-muted-foreground">
        Complete your booking - <span className="font-medium">No account required!</span>
      </p>
        </div>

        {postcodeServiceUnavailable && (
          <div className="mb-6 p-4 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-100">
            <p className="font-medium">Service not available for this postcode</p>
            <p className="text-sm mt-1">
              The selected service is not available for <strong>{formData.postcode.trim()}</strong>. Please change your address/postcode to an area we cover, or{' '}
              <button
                type="button"
                onClick={() => {
                  // Use the postcode from this page so /booking/services shows services for THIS address, not the old one
                  const pc = formData.postcode.trim()
                  if (pc && validateUKPostcode(pc)) {
                    setStorePostcode(normalizeUKPostcode(pc))
                  }
                  router.push('/booking/services')
                }}
                className="underline font-medium hover:no-underline"
              >
                go back to choose a different service
              </button>
              .
            </p>
          </div>
        )}

        {postcodeCheckLoading && (
          <p className="text-sm text-muted-foreground mb-4">Checking availability for your postcode…</p>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Personal Information</h2>

            <div>
              <label htmlFor="name" className="block text-sm font-medium mb-1">
                Full Name <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, name: e.target.value }))
                  if (errors.name) setErrors(prev => ({ ...prev, name: '' }))
                }}
                className={`w-full px-4 py-2 border rounded-lg ${
                  errors.name ? 'border-destructive' : 'border-border'
                }`}
                placeholder="John Doe"
              />
              {errors.name && <p className="text-sm text-destructive mt-1">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1">
                Email Address <span className="text-destructive">*</span>
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, email: e.target.value }))
                  if (errors.email) setErrors(prev => ({ ...prev, email: '' }))
                }}
                className={`w-full px-4 py-2 border rounded-lg ${
                  errors.email ? 'border-destructive' : 'border-border'
                }`}
                placeholder="john@example.com"
              />
              {errors.email && <p className="text-sm text-destructive mt-1">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium mb-1">
                Phone Number <span className="text-destructive">*</span>
              </label>
              <input
                type="tel"
                id="phone"
                value={formData.phone}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, phone: e.target.value }))
                  if (errors.phone) setErrors(prev => ({ ...prev, phone: '' }))
                }}
                className={`w-full px-4 py-2 border rounded-lg ${
                  errors.phone ? 'border-destructive' : 'border-border'
                }`}
                placeholder="07123456789"
              />
              {errors.phone && <p className="text-sm text-destructive mt-1">{errors.phone}</p>}
            </div>
          </div>

          {/* Address Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Service Address</h2>

            <div className="relative" ref={autocompleteRef}>
              <label htmlFor="address_search" className="block text-sm font-medium mb-1">
                Search Address <span className="text-muted-foreground text-xs">(or fill manually below)</span>
              </label>
              <input
                type="text"
                id="address_search"
                value={autocompleteQuery}
                onChange={(e) => {
                  const query = e.target.value
                  setAutocompleteQuery(query)
                  // Trigger search immediately as user types
                  if (query.length >= 2) {
                    handleAutocompleteSearch(query)
                  } else {
                    setAutocompleteSuggestions([])
                    setShowSuggestions(false)
                  }
                }}
                onFocus={() => {
                  // Show suggestions again if we have them and query is long enough
                  if (autocompleteQuery.length >= 2 && autocompleteSuggestions.length > 0) {
                    setShowSuggestions(true)
                  }
                }}
                className="w-full px-4 py-2 border border-border rounded-lg focus:border-primary focus:ring-2 focus:ring-primary/20"
                placeholder="Start typing your address or postcode (e.g., SW1A 1AA or 10 Downing Street)..."
              />
              {showSuggestions && autocompleteSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-background border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {autocompleteSuggestions.map((suggestion) => (
                    <button
                      key={suggestion.place_id}
                      type="button"
                      onClick={() => handleAddressSelect(suggestion)}
                      className="w-full text-left px-4 py-2 hover:bg-muted transition-colors border-b border-border last:border-b-0"
                    >
                      <div className="font-medium">{suggestion.structured_formatting?.main_text || suggestion.description}</div>
                      {suggestion.structured_formatting?.secondary_text && (
                        <div className="text-sm text-muted-foreground">
                          {suggestion.structured_formatting.secondary_text}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
              {autocompleteQuery && autocompleteQuery.length >= 2 && !showSuggestions && autocompleteSuggestions.length === 0 && (
                <div className="mt-2 text-sm text-muted-foreground bg-muted p-2 rounded">
                  <p>No results found for &quot;{autocompleteQuery}&quot;. You can fill the address fields manually below.</p>
                  <p className="text-xs mt-1">Tip: Try searching with just the postcode or street name (e.g., &quot;SW1A 1AA&quot; or &quot;Downing Street&quot;).</p>
                  <p className="text-xs mt-1 text-amber-600 dark:text-amber-400">
                    <strong>Note:</strong> If autocomplete never works, check that Google Maps API key is configured in backend/.env
                  </p>
                </div>
              )}
            </div>

            <div className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
              <p>
                <strong>Tip:</strong> Use the search above to quickly fill your address, or enter it manually in the fields below. 
                You can edit any field after selecting from the search results.
              </p>
            </div>

            <div>
              <label htmlFor="address_line1" className="block text-sm font-medium mb-1">
                Address Line 1 <span className="text-destructive">*</span>
              </label>
              <input
                type="text"
                id="address_line1"
                value={formData.address_line1}
                onChange={(e) => {
                  setFormData(prev => ({ ...prev, address_line1: e.target.value }))
                  if (errors.address_line1) setErrors(prev => ({ ...prev, address_line1: '' }))
                }}
                className={`w-full px-4 py-2 border rounded-lg ${
                  errors.address_line1 ? 'border-destructive' : 'border-border'
                }`}
                placeholder="House number and street name"
              />
              {errors.address_line1 && (
                <p className="text-sm text-destructive mt-1">{errors.address_line1}</p>
              )}
            </div>

            <div>
              <label htmlFor="address_line2" className="block text-sm font-medium mb-1">
                Address Line 2 <span className="text-muted-foreground text-xs">(Optional)</span>
              </label>
              <input
                type="text"
                id="address_line2"
                value={formData.address_line2}
                onChange={(e) => setFormData(prev => ({ ...prev, address_line2: e.target.value }))}
                className="w-full px-4 py-2 border border-border rounded-lg"
                placeholder="Apartment, suite, etc."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="block text-sm font-medium mb-1">
                  City <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  id="city"
                  value={formData.city}
                  onChange={(e) => {
                    setFormData(prev => ({ ...prev, city: e.target.value }))
                    if (errors.city) setErrors(prev => ({ ...prev, city: '' }))
                  }}
                  className={`w-full px-4 py-2 border rounded-lg ${
                    errors.city ? 'border-destructive' : 'border-border'
                  }`}
                  placeholder="London"
                />
                {errors.city && <p className="text-sm text-destructive mt-1">{errors.city}</p>}
              </div>

              <div>
                <label htmlFor="postcode" className="block text-sm font-medium mb-1">
                  Postcode <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  id="postcode"
                  value={formData.postcode}
                  onChange={(e) => {
                    setFormData(prev => ({ ...prev, postcode: e.target.value.toUpperCase() }))
                    if (errors.postcode) setErrors(prev => ({ ...prev, postcode: '' }))
                  }}
                  className={`w-full px-4 py-2 border rounded-lg ${
                    errors.postcode ? 'border-destructive' : 'border-border'
                  }`}
                  placeholder="SW1A 1AA"
                />
                {errors.postcode && (
                  <p className="text-sm text-destructive mt-1">{errors.postcode}</p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="country" className="block text-sm font-medium mb-1">
                Country
              </label>
              <input
                type="text"
                id="country"
                value={formData.country}
                disabled
                className="w-full px-4 py-2 border border-border rounded-lg bg-muted"
              />
            </div>
          </div>

          {/* Special Instructions */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium mb-1">
              Special Instructions <span className="text-muted-foreground text-xs">(Optional)</span>
            </label>
            <textarea
              id="notes"
              value={notes || ''}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-border rounded-lg"
              placeholder="Any special instructions for our staff..."
            />
          </div>

          {/* Validation Error */}
          {errors.submit && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
              {errors.submit}
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 px-6 py-3 border border-border rounded-lg hover:bg-muted transition-colors"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold disabled:opacity-50"
            >
              {loading ? 'Checking address…' : 'Confirm Your Details'}
            </button>
          </div>
        </form>

        {/* Guest Checkout Info */}
        <div className="mt-8 p-6 bg-muted rounded-lg">
          <h3 className="font-semibold mb-2">Guest Checkout Benefits:</h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            <li>No login or registration required</li>
            <li>Perfect for elderly customers</li>
            <li>All features work without an account</li>
            <li>Optional account linking after order completion</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
