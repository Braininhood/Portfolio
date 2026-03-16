/**
 * Customer Management Types
 */

export interface Customer {
  id: number;
  user?: number | null;
  user_email?: string | null;
  name: string;
  email: string;
  phone?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  postcode?: string | null;
  country?: string;
  address_validated?: boolean;
  notes?: string | null;
  tags?: string[];
  addresses?: Address[];
  created_at?: string;
  updated_at?: string;
}

export interface Address {
  id: number;
  customer?: number;
  type: 'billing' | 'service' | 'other';
  address_line1: string;
  address_line2?: string | null;
  city: string;
  postcode: string;
  country: string;
  is_default: boolean;
  address_validated: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CustomerListResponse {
  success: boolean;
  data: Customer[];
  meta: {
    count: number;
  };
}

export interface CustomerDetailResponse {
  success: boolean;
  data: Customer;
  meta?: Record<string, any>;
}

export interface CustomerCreateRequest {
  user?: number | null;
  name: string;
  email: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postcode?: string;
  country?: string;
  notes?: string;
  tags?: string[];
}

export interface CustomerUpdateRequest extends Partial<CustomerCreateRequest> {}

export interface CustomerBookingsResponse {
  success: boolean;
  data: {
    appointments: any[];
    orders: any[];
    subscriptions: any[];
  };
  meta: {
    appointments_count: number;
    orders_count: number;
    subscriptions_count: number;
  };
}

export interface CustomerPaymentsResponse {
  success: boolean;
  data: Array<{
    id: number;
    order_number: string;
    date: string;
    amount: number;
    status: string;
    order_status: string;
    type: string;
  }>;
  meta: {
    total_paid: number;
    total_pending: number;
    count: number;
  };
}
