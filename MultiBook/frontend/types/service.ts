/**
 * Service Management Types
 */

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  image?: string | null;
  position: number;
  is_active: boolean;
  services_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Service {
  id: number;
  category: Category;
  category_id: number;
  category_name?: string;
  name: string;
  slug: string;
  description?: string | null;
  duration: number;
  price: string | number;
  currency: string;
  image?: string | null;
  color: string;
  capacity: number;
  padding_time: number;
  position: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ServiceListResponse {
  success: boolean;
  data: Service[];
  meta: {
    count: number;
  };
}

export interface ServiceDetailResponse {
  success: boolean;
  data: Service;
  meta?: Record<string, any>;
}

export interface CategoryListResponse {
  success: boolean;
  data: Category[];
  meta: {
    count: number;
  };
}

export interface CategoryDetailResponse {
  success: boolean;
  data: Category;
  meta?: Record<string, any>;
}

export interface ServiceCreateRequest {
  category_id: number;
  name: string;
  description?: string;
  duration: number;
  price: number | string;
  currency?: string;
  image?: string | null;
  color?: string;
  capacity?: number;
  padding_time?: number;
  position?: number;
  is_active?: boolean;
}

export interface ServiceUpdateRequest extends Partial<ServiceCreateRequest> {}

export interface CategoryCreateRequest {
  name: string;
  description?: string;
  image?: string | null;
  position?: number;
  is_active?: boolean;
}

export interface CategoryUpdateRequest extends Partial<CategoryCreateRequest> {}

export interface ReorderRequest {
  services?: Array<{ id: number; position: number }>;
  categories?: Array<{ id: number; position: number }>;
}

/** API response for reorder endpoints */
export interface ReorderResponse {
  success: boolean;
}
