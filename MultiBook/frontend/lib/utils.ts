import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format UK postcode for display
 */
export function formatPostcode(postcode: string): string {
  return postcode.toUpperCase().trim()
}

/** UK postcode regex: 1–2 letters, digit, optional digit/letter, optional space, digit, 2 letters (no C,I,K,M,O,V) */
const UK_POSTCODE_PATTERN = /^[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][ABD-HJLNP-UW-Z]{2}$/i

/**
 * Normalize UK postcode for validation and display (trim, uppercase, single space)
 */
export function normalizeUKPostcode(postcode: string): string {
  return postcode.trim().toUpperCase().replace(/\s+/g, ' ')
}

/**
 * Validate UK postcode format (use normalized form for consistency)
 */
export function validateUKPostcode(postcode: string): boolean {
  return UK_POSTCODE_PATTERN.test(normalizeUKPostcode(postcode))
}

/**
 * Format UK phone number for display
 */
export function formatUKPhone(phone: string): string {
  // Remove all non-digits
  const digits = phone.replace(/\D/g, '')
  
  // Format based on length
  if (digits.startsWith('44') && digits.length === 12) {
    // International format: +44 20 1234 5678
    return `+44 ${digits.slice(2, 4)} ${digits.slice(4, 8)} ${digits.slice(8)}`
  } else if (digits.startsWith('0') && digits.length === 11) {
    // National format: 020 1234 5678
    return `${digits.slice(0, 3)} ${digits.slice(3, 7)} ${digits.slice(7)}`
  } else if (digits.length === 10) {
    // Mobile: 07700 900000
    return `${digits.slice(0, 5)} ${digits.slice(5)}`
  }
  
  return phone
}

/**
 * Format status for display (e.g. in_progress -> "In Progress")
 */
export function formatStatus(status: string): string {
  if (!status) return ''
  const map: Record<string, string> = {
    pending: 'Pending',
    confirmed: 'Confirmed',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
    no_show: 'No Show',
    partial: 'Partial Payment',
    paid: 'Paid',
    refunded: 'Refunded',
    pending_approval: 'Pending Approval',
    approved: 'Approved',
    rejected: 'Rejected',
  }
  return map[status.toLowerCase()] ?? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/**
 * Format currency (GBP)
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
  }).format(amount)
}

/**
 * Format date for display
 */
export function formatDate(date: Date | string, format: 'short' | 'long' | 'time' = 'short'): string {
  const d = typeof date === 'string' ? new Date(date) : date
  
  if (format === 'time') {
    return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }
  
  if (format === 'long') {
    return d.toLocaleDateString('en-GB', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }
  
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Check if cancellation/rescheduling is allowed (24h policy)
 */
export function canCancelOrReschedule(scheduledDate: Date | string): boolean {
  const scheduled = typeof scheduledDate === 'string' ? new Date(scheduledDate) : scheduledDate
  const now = new Date()
  const hoursUntilAppointment = (scheduled.getTime() - now.getTime()) / (1000 * 60 * 60)
  return hoursUntilAppointment >= 24
}

/**
 * Get cancellation deadline (24 hours before appointment)
 */
export function getCancellationDeadline(scheduledDate: Date | string): Date {
  const scheduled = typeof scheduledDate === 'string' ? new Date(scheduledDate) : scheduledDate
  return new Date(scheduled.getTime() - 24 * 60 * 60 * 1000)
}
