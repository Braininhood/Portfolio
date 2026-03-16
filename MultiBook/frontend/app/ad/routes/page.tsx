'use client'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { DashboardLayout } from '@/components/layouts/DashboardLayout'
import { apiClient } from '@/lib/api/client'
import { ADMIN_ENDPOINTS } from '@/lib/api/endpoints'
import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'

interface StopInput {
  address_line1: string
  city: string
  postcode: string
  label?: string
}

interface OrderedStop {
  index: number
  order_position: number
  lat: number
  lng: number
  label: string
  formatted_address: string
  travel_time_to_next_seconds: number | null
  travel_time_to_next_minutes: number | null
}

interface RouteResult {
  ordered_stops: OrderedStop[]
  order_indices: number[]
  leg_durations_seconds: number[]
  total_duration_seconds: number
  total_duration_minutes: number
  points: { lat: number; lng: number; label: string }[]
}

interface StaffOption {
  id: number
  name: string
  email: string
}

declare global {
  interface Window {
    google?: typeof google
  }
}

/**
 * Route Optimization Page (Week 11 Day 1-2)
 * GET staff day appointments -> optimize visit order -> map + travel times
 */
export default function RouteOptimizationPage() {
  const [staffList, setStaffList] = useState<StaffOption[]>([])
  const [staffId, setStaffId] = useState<string>('')
  const [routeDate, setRouteDate] = useState(() => new Date().toISOString().split('T')[0])
  const [stops, setStops] = useState<StopInput[]>([])
  const [result, setResult] = useState<RouteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadDayLoading, setLoadDayLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<google.maps.Map | null>(null)
  const markersRef = useRef<google.maps.Marker[]>([])
  const polylineRef = useRef<google.maps.Polyline | null>(null)

  useEffect(() => {
    apiClient
      .get<{ results?: { id: number; name: string; email: string }[] }>(ADMIN_ENDPOINTS.STAFF.LIST)
      .then((res) => {
        const list = (res.data as { results?: StaffOption[] })?.results ?? (res.data as unknown as StaffOption[])
        setStaffList(Array.isArray(list) ? list : [])
      })
      .catch(() => setStaffList([]))
  }, [])

  const loadStaffDay = async () => {
    if (!staffId || !routeDate) {
      setError('Select staff and date')
      return
    }
    setLoadDayLoading(true)
    setError(null)
    try {
      const res = await apiClient.get<{ success: boolean; data: { stops: StopInput[] } }>(
        `${ADMIN_ENDPOINTS.ROUTES.STAFF_DAY}?staff_id=${staffId}&date=${routeDate}`
      )
      if (res.data.success && res.data.data?.stops) {
        setStops(
          res.data.data.stops.map((s: StopInput & { appointment_id?: number }) => ({
            address_line1: s.address_line1 || '',
            city: s.city || '',
            postcode: s.postcode || '',
            label: s.label || `#${s.appointment_id || ''}`,
          }))
        )
        setResult(null)
      } else {
        setStops([])
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load staff day')
    } finally {
      setLoadDayLoading(false)
    }
  }

  const addStop = () => {
    setStops((prev) => [...prev, { address_line1: '', city: '', postcode: '' }])
  }

  const removeStop = (i: number) => {
    setStops((prev) => prev.filter((_, idx) => idx !== i))
    setResult(null)
  }

  const updateStop = (i: number, field: keyof StopInput, value: string) => {
    setStops((prev) => prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s)))
    setResult(null)
  }

  const optimize = async () => {
    const valid = stops.filter((s) => (s.address_line1 || s.postcode || '').trim())
    if (valid.length === 0) {
      setError('Add at least one stop with address or postcode')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.post<{ success: boolean; data: RouteResult }>(
        ADMIN_ENDPOINTS.ROUTES.OPTIMIZE,
        { stops: valid }
      )
      if (res.data.success && res.data.data) {
        setResult(res.data.data)
      } else {
        setError('Optimization failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Optimization failed')
    } finally {
      setLoading(false)
    }
  }

  // Draw map when result changes
  useEffect(() => {
    if (!result?.points?.length || !mapRef.current) return
    const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    if (!key) return

    const drawMap = () => {
      if (!window.google?.maps) return
      if (!mapInstanceRef.current) {
        const center = result.points[0]
        mapInstanceRef.current = new window.google.maps.Map(mapRef.current!, {
          center: { lat: center.lat, lng: center.lng },
          zoom: 11,
        })
      }
      const map = mapInstanceRef.current
      markersRef.current.forEach((m) => m.setMap(null))
      markersRef.current = []
      result.ordered_stops.forEach((stop, i) => {
        const m = new window.google!.maps.Marker({
          position: { lat: stop.lat, lng: stop.lng },
          map,
          label: { text: String(i + 1), color: 'white' },
          title: stop.label || stop.formatted_address,
        })
        markersRef.current.push(m)
      })
      if (polylineRef.current) polylineRef.current.setMap(null)
      const path = result.ordered_stops.map((s) => ({ lat: s.lat, lng: s.lng }))
      polylineRef.current = new window.google!.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: '#1976d2',
        strokeOpacity: 1,
        strokeWeight: 4,
        map,
      })
      const bounds = new window.google!.maps.LatLngBounds()
      path.forEach((p) => bounds.extend(p))
      map.fitBounds(bounds, 40)
    }

    if (window.google?.maps) {
      drawMap()
      return
    }
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${key}&loading=async`
    script.async = true
    script.onload = drawMap
    document.head.appendChild(script)
    return () => {
      markersRef.current.forEach((m) => m.setMap(null))
      if (polylineRef.current) polylineRef.current.setMap(null)
    }
  }, [result])

  return (
    <ProtectedRoute requiredRole="admin">
      <DashboardLayout>
        <div className="container mx-auto p-4 sm:p-6 md:p-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Route Optimization</h1>
              <p className="text-muted-foreground mt-1">
                Multi-stop routing, distance calculation, estimated travel time
              </p>
            </div>
            <Link href="/ad/dashboard" className="text-primary hover:underline">
              ← Dashboard
            </Link>
          </div>

          {/* Load staff day */}
          <section className="bg-card border rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Load staff day</h2>
            <div className="flex flex-wrap gap-4 items-end">
              <label className="flex flex-col gap-1">
                <span className="text-sm font-medium">Staff</span>
                <select
                  value={staffId}
                  onChange={(e) => setStaffId(e.target.value)}
                  className="border rounded px-3 py-2 min-w-[200px]"
                >
                  <option value="">Select staff</option>
                  {staffList.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm font-medium">Date</span>
                <input
                  type="date"
                  value={routeDate}
                  onChange={(e) => setRouteDate(e.target.value)}
                  className="border rounded px-3 py-2"
                />
              </label>
              <button
                onClick={loadStaffDay}
                disabled={loadDayLoading}
                className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
              >
                {loadDayLoading ? 'Loading...' : 'Load day'}
              </button>
            </div>
          </section>

          {/* Stops list */}
          <section className="bg-card border rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Stops</h2>
              <button
                type="button"
                onClick={addStop}
                className="text-sm text-primary hover:underline"
              >
                + Add stop
              </button>
            </div>
            <div className="space-y-3">
              {stops.map((stop, i) => (
                <div key={i} className="flex flex-wrap gap-2 items-center p-3 border rounded bg-muted/30">
                  <span className="text-sm font-medium w-8">#{i + 1}</span>
                  <input
                    placeholder="Address line 1"
                    value={stop.address_line1}
                    onChange={(e) => updateStop(i, 'address_line1', e.target.value)}
                    className="border rounded px-2 py-1 flex-1 min-w-[120px]"
                  />
                  <input
                    placeholder="City"
                    value={stop.city}
                    onChange={(e) => updateStop(i, 'city', e.target.value)}
                    className="border rounded px-2 py-1 w-28"
                  />
                  <input
                    placeholder="Postcode"
                    value={stop.postcode}
                    onChange={(e) => updateStop(i, 'postcode', e.target.value)}
                    className="border rounded px-2 py-1 w-24"
                  />
                  <button
                    type="button"
                    onClick={() => removeStop(i)}
                    className="text-destructive hover:underline text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={optimize}
              disabled={loading || stops.length === 0}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Optimizing...' : 'Optimize route'}
            </button>
          </section>

          {error && (
            <div className="mb-6 p-4 bg-destructive/10 text-destructive rounded-lg">
              {error}
            </div>
          )}

          {result && (
            <>
              <section className="bg-card border rounded-lg p-6 mb-6">
                <h2 className="text-lg font-semibold mb-2">Optimized order & travel times</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Total estimated travel time: <strong>{result.total_duration_minutes} min</strong>
                </p>
                <ul className="space-y-2">
                  {result.ordered_stops.map((s) => (
                    <li key={s.index} className="flex items-center gap-4 py-2 border-b border-border/50">
                      <span className="font-medium w-8">#{s.order_position}</span>
                      <span className="flex-1">{s.formatted_address || s.label}</span>
                      {s.travel_time_to_next_minutes != null && (
                        <span className="text-muted-foreground text-sm">
                          → {s.travel_time_to_next_minutes} min to next
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
              <section className="bg-card border rounded-lg p-6">
                <h2 className="text-lg font-semibold mb-4">Map</h2>
                <div
                  ref={mapRef}
                  className="w-full h-[400px] rounded border bg-muted"
                  style={{ minHeight: 400 }}
                />
                {!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY in .env.local for map display.
                  </p>
                )}
              </section>
            </>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  )
}
