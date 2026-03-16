'use client'

import { useEffect, useRef, useState } from 'react'
import { apiClient } from '@/lib/api/client'
import type { StaffArea } from '@/types/staff'

interface ServiceAreaMapProps {
  areas: StaffArea[]
  centerPostcode?: string
  onAreaClick?: (area: StaffArea) => void
}

interface MapCoordinates {
  lat: number
  lng: number
}

export function ServiceAreaMap({ areas, centerPostcode, onAreaClick }: ServiceAreaMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<google.maps.Map | null>(null)
  const [circles, setCircles] = useState<google.maps.Circle[]>([])
  const [markers, setMarkers] = useState<google.maps.Marker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState<string | null>(null)

  // Get Google Maps API key from backend
  useEffect(() => {
    const fetchApiKey = async () => {
      try {
        // Try to get API key from backend config endpoint
        const response = await apiClient.get('/addr/config/')
        if (response.data.success && response.data.data?.api_key) {
          setApiKey(response.data.data.api_key)
        } else {
          // Fallback: try to get from environment (if exposed)
          const envKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
          if (envKey) {
            setApiKey(envKey)
          } else {
            setError('Google Maps API key not configured. Please add GOOGLE_MAPS_API_KEY to backend/.env')
            setLoading(false)
          }
        }
      } catch (_err) {
        // Fallback: try environment variable
        const envKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
        if (envKey) {
          setApiKey(envKey)
        } else {
          setError('Google Maps API key not available. Please configure GOOGLE_MAPS_API_KEY in backend/.env')
          setLoading(false)
        }
      }
    }
    fetchApiKey()
  }, [])

  // Load Google Maps script
  useEffect(() => {
    if (!apiKey || !mapRef.current) return

    // Check if script is already loaded
    if (window.google && window.google.maps) {
      // Wait a bit for areas to be ready
      setTimeout(() => initializeMap(), 100)
      return
    }

    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry&loading=async`
    script.async = true
    script.defer = true
    script.onload = () => {
      // Wait a bit for areas to be ready
      setTimeout(() => initializeMap(), 100)
    }
    script.onerror = () => {
      setError('Failed to load Google Maps')
      setLoading(false)
    }
    document.head.appendChild(script)

    return () => {
      // Cleanup: remove script if component unmounts
      const existingScript = document.querySelector(`script[src*="maps.googleapis.com"]`)
      if (existingScript) {
        // Don't remove - might be used by other components
      }
    }
  }, [apiKey, areas])

  // Initialize map and draw areas
  const initializeMap = async () => {
    if (!mapRef.current || !window.google) return

    try {
      setLoading(true)

      // Get center coordinates
      let center: MapCoordinates = { lat: 51.5074, lng: -0.1278 } // Default: London
      const bounds = new google.maps.LatLngBounds()

      // Geocode areas to get coordinates
      const areaCoordinates: Array<{ area: StaffArea; coords: MapCoordinates }> = []

      // Geocode all areas in parallel
      const geocodePromises = areas.map(async (area) => {
        try {
          const response = await apiClient.get('/addr/validate/', {
            params: { postcode: area.postcode },
          })

          if (response.data.success && response.data.data) {
            const data = response.data.data
            if (data.lat && data.lng) {
              return {
                area,
                coords: { lat: parseFloat(data.lat), lng: parseFloat(data.lng) },
              }
            }
          }
        } catch (err) {
          console.error(`Error geocoding ${area.postcode}:`, err)
        }
        return null
      })

      const results = await Promise.all(geocodePromises)
      results.forEach((result) => {
        if (result) {
          areaCoordinates.push(result)
          bounds.extend(result.coords)
          
          // Use first area as center, or centerPostcode if provided
          if (centerPostcode === result.area.postcode || areaCoordinates.length === 1) {
            center = result.coords
          }
        }
      })

      // If centerPostcode is provided, geocode it
      if (centerPostcode && !areas.find(a => a.postcode === centerPostcode)) {
        try {
          const response = await apiClient.get('/addr/validate/', {
            params: { postcode: centerPostcode },
          })
          if (response.data.success && response.data.data?.lat && response.data.data?.lng) {
            center = {
              lat: parseFloat(response.data.data.lat),
              lng: parseFloat(response.data.data.lng),
            }
            bounds.extend(center)
          }
        } catch (err) {
          console.error(`Error geocoding center postcode ${centerPostcode}:`, err)
        }
      }

      // Create map
      const mapInstance = new google.maps.Map(mapRef.current, {
        center,
        zoom: areaCoordinates.length > 0 ? 10 : 6,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }],
          },
        ],
      })

      // Fit bounds if we have areas
      if (areaCoordinates.length > 0) {
        mapInstance.fitBounds(bounds)
        // Ensure minimum zoom
        google.maps.event.addListenerOnce(mapInstance, 'bounds_changed', () => {
          if (mapInstance.getZoom()! > 15) {
            mapInstance.setZoom(15)
          }
        })
      }

      setMap(mapInstance)

      // Draw circles for each area
      const newCircles: google.maps.Circle[] = []
      const newMarkers: google.maps.Marker[] = []

      areaCoordinates.forEach(({ area, coords }) => {
        // Create circle
        const circle = new google.maps.Circle({
          strokeColor: area.is_active ? '#3B82F6' : '#9CA3AF',
          strokeOpacity: 0.8,
          strokeWeight: 2,
          fillColor: area.is_active ? '#3B82F6' : '#9CA3AF',
          fillOpacity: 0.15,
          map: mapInstance,
          center: coords,
          radius: area.radius_miles * 1609.34, // Convert miles to meters (1 mile = 1609.34 meters)
          clickable: true,
        })

        // Add click handler
        if (onAreaClick) {
          circle.addListener('click', () => {
            onAreaClick(area)
          })
        }

        newCircles.push(circle)

        // Create marker for center
        const marker = new google.maps.Marker({
          position: coords,
          map: mapInstance,
          title: `${area.postcode} (${area.radius_miles} miles)`,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 8,
            fillColor: area.is_active ? '#3B82F6' : '#9CA3AF',
            fillOpacity: 1,
            strokeColor: '#FFFFFF',
            strokeWeight: 2,
          },
        })

        // Add info window
        const infoWindow = new google.maps.InfoWindow({
          content: `
            <div style="padding: 8px;">
              <strong>${area.postcode}</strong><br/>
              Radius: ${area.radius_miles} miles<br/>
              Status: ${area.is_active ? 'Active' : 'Inactive'}
            </div>
          `,
        })

        marker.addListener('click', () => {
          infoWindow.open(mapInstance, marker)
          if (onAreaClick) {
            onAreaClick(area)
          }
        })

        newMarkers.push(marker)
      })

      // Add center postcode marker if provided and different
      if (centerPostcode && !areas.find(a => a.postcode === centerPostcode)) {
        try {
          const response = await apiClient.get('/addr/validate/', {
            params: { postcode: centerPostcode },
          })
          if (response.data.success && response.data.data?.lat && response.data.data?.lng) {
            const centerCoords = {
              lat: parseFloat(response.data.data.lat),
              lng: parseFloat(response.data.data.lng),
            }

            const centerMarker = new google.maps.Marker({
              position: centerCoords,
              map: mapInstance,
              title: `Center: ${centerPostcode}`,
              icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: '#EF4444',
                fillOpacity: 1,
                strokeColor: '#FFFFFF',
                strokeWeight: 2,
              },
            })

            newMarkers.push(centerMarker)
          }
        } catch (err) {
          console.error('Error adding center marker:', err)
        }
      }

      setCircles(newCircles)
      setMarkers(newMarkers)
      setLoading(false)
    } catch (err) {
      console.error('Error initializing map:', err)
      setError('Failed to initialize map')
      setLoading(false)
    }
  }

  // Update map when areas change (only if map is already initialized)
  useEffect(() => {
    if (map && window.google && areas.length > 0) {
      // Clear existing circles and markers
      circles.forEach(circle => circle.setMap(null))
      markers.forEach(marker => marker.setMap(null))

      // Reinitialize with new areas
      initializeMap()
    }
  }, [areas])

  if (error) {
    return (
      <div className="border rounded-lg p-8 text-center bg-muted">
        <p className="text-destructive">{error}</p>
        <p className="text-sm text-muted-foreground mt-2">
          Please configure NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in your .env.local file
        </p>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full min-h-[400px]">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/50 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading map...</p>
          </div>
        </div>
      )}
      <div ref={mapRef} className="w-full h-full rounded-lg" style={{ minHeight: '400px' }} />
      
      {/* Legend */}
      {!loading && areas.length > 0 && (
        <div className="absolute top-4 right-4 bg-white border rounded-lg p-3 shadow-lg z-10">
          <div className="text-sm font-medium mb-2">Legend</div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500 opacity-30 border-2 border-blue-500"></div>
              <span>Active Area</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-gray-400 opacity-30 border-2 border-gray-400"></div>
              <span>Inactive Area</span>
            </div>
            {centerPostcode && (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-red-500"></div>
                <span>Center Postcode</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
