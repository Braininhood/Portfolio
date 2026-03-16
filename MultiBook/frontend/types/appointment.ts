/**
 * Appointment/Job Types for Staff Portal
 */

export interface Appointment {
  id: number;
  staff?: {
    id: number;
    name: string;
    email: string;
  };
  staff_id: number;
  service?: {
    id: number;
    name: string;
    duration: number;
    price: number;
  };
  service_id: number;
  start_time: string;
  end_time: string;
  status: 'pending' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  appointment_type: 'single' | 'subscription' | 'order_item';
  subscription?: number | null;
  subscription_number?: string | null;
  subscription_id?: number | null;
  order?: number | null;
  order_number?: string | null;
  order_id?: number | null;
  calendar_event_id?: Record<string, string>;
  calendar_synced_to?: string[];
  internal_notes?: string | null;
  location_notes?: string | null;
  /** Job completion photos (Supabase Storage): list of { url, path, uploaded_at } */
  completion_photos?: Array<{ url: string; path?: string; uploaded_at?: string }>;
  created_at?: string;
  updated_at?: string;
  customer_booking?: CustomerAppointment;
}

export interface CustomerAppointment {
  id: number;
  customer?: {
    id: number;
    name: string;
    email: string;
    phone?: string;
  };
  customer_id: number;
  appointment_id: number;
  number_of_persons: number;
  extras?: any[];
  custom_fields?: Record<string, any>;
  total_price: string | number;
  deposit_paid: string | number;
  payment_status: 'pending' | 'partial' | 'paid' | 'refunded';
  cancellation_token?: string;
  cancellation_policy_hours: number;
  cancellation_deadline?: string;
  can_cancel: boolean;
  can_reschedule: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AppointmentListResponse {
  success: boolean;
  data: Appointment[];
  meta: {
    count: number;
  };
}

export interface AppointmentDetailResponse {
  success: boolean;
  data: Appointment;
  meta?: Record<string, any>;
}

export interface StaffSchedule {
  id: number;
  staff?: number;
  day_of_week: number;
  day_name?: string;
  start_time: string;
  end_time: string;
  breaks: Array<{ start: string; end: string }>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface StaffScheduleResponse {
  success: boolean;
  data: StaffSchedule[];
  meta?: Record<string, any>;
}
