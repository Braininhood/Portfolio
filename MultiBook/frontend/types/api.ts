/**
 * API Response Types
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp?: string;
    version?: string;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Authentication Types
 */
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    role: 'admin' | 'manager' | 'staff' | 'customer';
    name?: string;
  };
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  name: string;
  phone?: string;
  role?: 'customer';
}

/**
 * Booking Types (Guest Checkout Supported)
 */
export interface BookingRequest {
  postcode: string;
  service_id: number;
  staff_id?: number;
  date: string;
  time: string;
  guest_email?: string;  // For guest checkout
  guest_name?: string;
  guest_phone?: string;
  address?: AddressData;
  notes?: string;
}

export interface OrderRequest {
  postcode: string;
  services: Array<{
    service_id: number;
    quantity?: number;
    staff_id?: number;
  }>;
  scheduled_date: string;
  scheduled_time?: string;
  guest_email?: string;  // For guest checkout
  guest_name?: string;
  guest_phone?: string;
  address?: AddressData;
  notes?: string;
}

export interface SubscriptionRequest {
  postcode: string;
  service_id: number;
  staff_id?: number;
  frequency: 'weekly' | 'biweekly' | 'monthly';
  duration_months: number;
  start_date: string;
  guest_email?: string;  // For guest checkout
  guest_name?: string;
  guest_phone?: string;
  address?: AddressData;
}

export interface AddressData {
  line1: string;
  line2?: string;
  city: string;
  postcode: string;
  country?: string;
}

/**
 * Guest Order/Subscription Access
 */
export interface GuestOrderAccess {
  order_number: string;
  email: string;
}

export interface GuestOrderLinkRequest {
  order_number: string;
  email: string;
  password?: string;  // For login
  register?: boolean;  // For registration
}
