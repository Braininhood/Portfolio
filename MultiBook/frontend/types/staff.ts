/**
 * Staff Management Types
 */

export interface StaffArea {
  id?: number;
  staff?: number;
  postcode: string;
  radius_miles: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface StaffSchedule {
  id?: number;
  staff?: number;
  day_of_week: number; // 0=Monday, 6=Sunday
  day_name?: string;
  start_time: string; // HH:MM format
  end_time: string; // HH:MM format
  breaks: Array<{ start: string; end: string }>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface StaffService {
  id?: number;
  staff?: number;
  service: {
    id: number;
    name: string;
    price: number;
    duration: number;
  };
  service_id: number;
  service_name?: string;
  price_override?: number | null;
  duration_override?: number | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Staff {
  id: number;
  user?: number | null;
  user_email?: string | null;
  name: string;
  email: string;
  phone?: string | null;
  photo?: string | null;
  bio?: string | null;
  services?: StaffService[];
  schedules?: StaffSchedule[];
  service_areas?: StaffArea[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface StaffListResponse {
  success: boolean;
  data: Staff[];
  meta: {
    count: number;
  };
}

export interface StaffDetailResponse {
  success: boolean;
  data: Staff;
  meta?: Record<string, any>;
}

export interface StaffCreateRequest {
  user?: number | null;
  name: string;
  email: string;
  phone?: string;
  photo?: string | null;
  bio?: string | null;
  is_active?: boolean;
}

export interface StaffUpdateRequest extends Partial<StaffCreateRequest> {}

export interface StaffAreaCreateRequest {
  staff: number;
  postcode: string;
  radius_miles: number;
  is_active?: boolean;
}

export interface StaffAreaUpdateRequest extends Partial<StaffAreaCreateRequest> {}

export interface StaffScheduleCreateRequest {
  staff: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  breaks?: Array<{ start: string; end: string }>;
  is_active?: boolean;
}

export interface StaffScheduleUpdateRequest extends Partial<StaffScheduleCreateRequest> {}

export interface StaffServiceCreateRequest {
  staff: number;
  service_id: number;
  price_override?: number | null;
  duration_override?: number | null;
  is_active?: boolean;
}

export interface StaffServiceUpdateRequest extends Partial<StaffServiceCreateRequest> {}
