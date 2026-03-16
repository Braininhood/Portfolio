/**
 * Booking Store (Zustand)
 * 
 * State management for the booking flow (guest checkout supported).
 */
'use client'

import { create } from 'zustand'
import type { AddressData } from '@/types/api'

interface BookingState {
  // Step 1: Postcode
  postcode: string | null
  
  // Step 2: Service Selection
  selectedService: number | null
  selectedServices: number[]  // For multi-service orders
  bookingType: 'single' | 'subscription' | 'order' | null
  
  // Step 3: Date & Time
  selectedDate: string | null
  selectedTime: string | null
  selectedStaff: number | null
  
  // Step 4: Booking Type Details
  subscriptionFrequency: 'weekly' | 'biweekly' | 'monthly' | null
  subscriptionDuration: number | null
  orderServices: Array<{
    service_id: number
    quantity: number
    staff_id?: number
  }>
  
  // Step 5: Guest Details (NO LOGIN REQUIRED; pre-fill when logged in)
  guestEmail: string | null
  guestName: string | null
  guestPhone: string | null
  address: AddressData | null
  notes: string | null
  /** Set when logged-in customer pre-fills details (for order creation) */
  customerId: number | null

  // Actions
  setPostcode: (postcode: string) => void
  setCustomerId: (id: number | null) => void
  setSelectedService: (serviceId: number | null) => void
  addServiceToOrder: (serviceId: number, quantity?: number) => void
  removeServiceFromOrder: (serviceId: number) => void
  setBookingType: (type: 'single' | 'subscription' | 'order' | null) => void
  setDateAndTime: (date: string, time: string, staffId?: number) => void
  setSubscriptionDetails: (frequency: 'weekly' | 'biweekly' | 'monthly', duration: number) => void
  setGuestDetails: (email: string, name: string, phone: string, address: AddressData) => void
  setNotes: (notes: string) => void
  resetBooking: () => void
}

const initialState = {
  postcode: null,
  selectedService: null,
  selectedServices: [],
  bookingType: null,
  selectedDate: null,
  selectedTime: null,
  selectedStaff: null,
  subscriptionFrequency: null,
  subscriptionDuration: null,
  orderServices: [],
  guestEmail: null,
  guestName: null,
  guestPhone: null,
  address: null,
  notes: null,
  customerId: null,
}

export const useBookingStore = create<BookingState>((set) => ({
  ...initialState,

  setPostcode: (postcode) => set({ postcode }),

  setSelectedService: (serviceId) => set({ selectedService: serviceId }),

  addServiceToOrder: (serviceId, quantity = 1) =>
    set((state) => ({
      orderServices: [
        ...state.orderServices.filter((s) => s.service_id !== serviceId),
        { service_id: serviceId, quantity },
      ],
    })),

  removeServiceFromOrder: (serviceId) =>
    set((state) => ({
      orderServices: state.orderServices.filter((s) => s.service_id !== serviceId),
    })),

  setBookingType: (type) => set({ bookingType: type }),

  setDateAndTime: (date, time, staffId) =>
    set({ selectedDate: date, selectedTime: time, selectedStaff: staffId }),

  setSubscriptionDetails: (frequency, duration) =>
    set({ subscriptionFrequency: frequency, subscriptionDuration: duration }),

  setGuestDetails: (email, name, phone, address) =>
    set({ guestEmail: email, guestName: name, guestPhone: phone, address }),

  setCustomerId: (id) => set({ customerId: id }),

  setNotes: (notes) => set({ notes }),

  resetBooking: () => set(initialState),
}))
