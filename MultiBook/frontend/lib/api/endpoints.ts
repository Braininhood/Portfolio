/**
 * API Endpoints Configuration
 * 
 * All endpoints use security prefixes as documented in MULTIBOOK_BEST_SOLUTION.md
 */

// Public Endpoints (No authentication required)
export const PUBLIC_ENDPOINTS = {
  // Services (Security: /api/svc/)
  SERVICES: {
    LIST: '/svc/',
    DETAIL: (id: string | number) => `/svc/${id}/`,
    BY_POSTCODE: '/svc/by-postcode/',
  },
  
  // Staff (Public listing) (Security: /api/stf/)
  STAFF: {
    LIST: '/stf/',
    BY_POSTCODE: '/stf/by-postcode/',
    DETAIL: (id: string | number) => `/stf/${id}/`,
  },
  
  // Coupons (Security: /api/coupons/)
  COUPONS: {
    LIST: '/coupons/',
    ACTIVE: '/coupons/active/',
    VALIDATE: '/coupons/validate/',
    DETAIL: (id: string | number) => `/coupons/${id}/`,
  },
  
  // Bookings/Orders (Security: /api/bkg/)
  BOOKINGS: {
    CREATE: '/bkg/',
    SUBSCRIPTION: '/bkg/subscription/',
    /** Create subscription (recurring booking) - POST */
    SUBSCRIPTIONS_CREATE: '/bkg/subscriptions/',
    ORDER: '/bkg/orders/',
    CANCEL: (id: string | number) => `/bkg/${id}/cancel/`,
    
    // Guest order access (NO AUTH REQUIRED)
    GUEST_ORDER: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/`,
    GUEST_ORDER_VERIFY: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/verify/`,
    GUEST_ORDER_TRACK: (token: string) => `/bkg/guest/order/token/${token}/`,
    GUEST_ORDER_CANCEL: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/cancel/`,
    GUEST_ORDER_REQUEST_CHANGE: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/request-change/`,
    GUEST_ORDER_LINK_LOGIN: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/link-login/`,
    GUEST_ORDER_LINK_REGISTER: (orderNumber: string) => `/bkg/guest/order/${orderNumber}/link-register/`,
    
    // Guest subscription access (NO AUTH REQUIRED)
    GUEST_SUBSCRIPTION: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/`,
    GUEST_SUBSCRIPTION_VERIFY: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/verify/`,
    GUEST_SUBSCRIPTION_TRACK: (token: string) => `/bkg/guest/subscription/token/${token}/`,
    GUEST_SUBSCRIPTION_PAUSE: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/pause/`,
    GUEST_SUBSCRIPTION_CANCEL: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/cancel/`,
    GUEST_SUBSCRIPTION_APPOINTMENT_CANCEL: (subscriptionNumber: string, apptId: string | number) => 
      `/bkg/guest/subscription/${subscriptionNumber}/appointments/${apptId}/cancel/`,
    GUEST_SUBSCRIPTION_LINK_LOGIN: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/link-login/`,
    GUEST_SUBSCRIPTION_LINK_REGISTER: (subscriptionNumber: string) => `/bkg/guest/subscription/${subscriptionNumber}/link-register/`,
    
    // Account linking check
    GUEST_CHECK_EMAIL: '/bkg/guest/check-email/',
  },
  
  // Address (Security: /api/addr/)
  ADDRESS: {
    AUTOCOMPLETE: '/addr/autocomplete/',
    VALIDATE: '/addr/validate/',
  },
  
  // Authentication (Security: /api/aut/)
  AUTH: {
    LOGIN: '/aut/login/',
    GOOGLE: '/aut/google/',
    GOOGLE_START: '/aut/google/start/',
    GOOGLE_CALLBACK: '/aut/google/callback/',
    REGISTER: '/aut/register/',
    LOGOUT: '/aut/logout/',
    REFRESH: '/aut/refresh/',
    PASSWORD_RESET: '/aut/password-reset/',
    CHECK_EMAIL: '/aut/check-email/',
  },
  
  // Available Slots (Security: /api/slots/)
  SLOTS: {
    AVAILABLE: '/slots/',
  },
  
  // Payments (Security: /api/pay/)
  PAYMENTS: {
    CREATE_INTENT: '/pay/create-intent/',
    CONFIRM: '/pay/confirm/',
    WEBHOOK: '/pay/webhook/',
  },
};

// Protected Endpoints (Authentication required)

// Customer Endpoints (Security: /api/cus/)
export const CUSTOMER_ENDPOINTS = {
  APPOINTMENTS: {
    LIST: '/cus/appointments/',
    DETAIL: (id: string | number) => `/cus/appointments/${id}/`,
    CANCEL: (id: string | number) => `/cus/appointments/${id}/cancel/`,
    RESCHEDULE: (id: string | number) => `/cus/appointments/${id}/reschedule/`,
    AVAILABLE_SLOTS: (id: string | number) => `/cus/appointments/${id}/available-slots/`,
  },
  
  SUBSCRIPTIONS: {
    LIST: '/cus/subscriptions/',
    CREATE: '/cus/subscriptions/',
    DETAIL: (id: string | number) => `/cus/subscriptions/${id}/`,
    UPDATE: (id: string | number) => `/cus/subscriptions/${id}/`,
    PAUSE: (id: string | number) => `/cus/subscriptions/${id}/pause/`,
    ACTIVATE: (id: string | number) => `/cus/subscriptions/${id}/activate/`,
    CANCEL: (id: string | number) => `/cus/subscriptions/${id}/cancel/`,
    APPOINTMENT_CANCEL: (id: string | number, apptId: string | number) =>
      `/cus/subscriptions/${id}/appointments/${apptId}/cancel/`,
    APPOINTMENT_REQUEST_CHANGE: (id: string | number, apptId: string | number) =>
      `/cus/subscriptions/${id}/appointments/${apptId}/request-change/`,
  },
  
  ORDERS: {
    LIST: '/cus/orders/',
    CREATE: '/cus/orders/',
    DETAIL: (id: string | number) => `/cus/orders/${id}/`,
    REQUEST_CHANGE: (id: string | number) => `/cus/orders/${id}/request-change/`,
    CANCEL: (id: string | number) => `/cus/orders/${id}/cancel/`,
    STATUS: (id: string | number) => `/cus/orders/${id}/status/`,
  },
  
  PROFILE: {
    GET: '/cus/profile/',
    UPDATE: (id: string | number) => `/cus/profile/${id}/`,
  },
  
  INVOICES: {
    LIST: '/cus/invoices/',
  },
  
  CALENDAR: {
    CONNECT: '/cus/calendar/connect/',
    STATUS: '/cus/calendar/status/',
    SYNC: '/cus/calendar/sync/',
    DISCONNECT: '/cus/calendar/disconnect/',
    EVENTS: '/cus/calendar/events/',
    ADD_EVENT: '/cus/calendar/add-event/',
  },
};

// Staff Endpoints (Security: /api/st/)
export const STAFF_ENDPOINTS = {
  SCHEDULE: '/st/schedule/',
  JOBS: {
    LIST: '/st/jobs/',
    DETAIL: (id: string | number) => `/st/jobs/${id}/`,
    CHECKIN: (id: string | number) => `/st/jobs/${id}/checkin/`,
    COMPLETE: (id: string | number) => `/st/jobs/${id}/complete/`,
    UPLOAD_PHOTO: (id: string | number) => `/st/jobs/${id}/upload-photo/`,
  },
  AVAILABILITY: {
    GET: '/st/availability/',
    UPDATE: '/st/availability/',
  },
  SERVICES: {
    LIST: '/st/services/',
    DETAIL: (id: string | number) => `/st/services/${id}/`,
    CREATE: '/st/services/',
    UPDATE: (id: string | number) => `/st/services/${id}/`,
    DELETE: (id: string | number) => `/st/services/${id}/`,
  },
  AREAS: {
    LIST: '/st/areas/',
    DETAIL: (id: string | number) => `/st/areas/${id}/`,
    CREATE: '/st/areas/',
    UPDATE: (id: string | number) => `/st/areas/${id}/`,
    DELETE: (id: string | number) => `/st/areas/${id}/`,
  },
  CATEGORIES: {
    LIST: '/st/categories/',
  },
  // Note: Calendar endpoints are shared across all roles. Use CALENDAR_ENDPOINTS instead.
  // These endpoints below point to non-existent routes - kept for reference but not used.
  CALENDAR: {
    CONNECT: '/calendar/google/connect/', // Use CALENDAR_ENDPOINTS.GOOGLE_CONNECT instead
    STATUS: '/calendar/status/', // Use CALENDAR_ENDPOINTS.STATUS instead
    SYNC: '/calendar/sync/', // Use CALENDAR_ENDPOINTS.SYNC instead
    DISCONNECT: '/calendar/google/disconnect/', // Use CALENDAR_ENDPOINTS.GOOGLE_DISCONNECT instead
    EVENTS: '/calendar/events/', // Use CALENDAR_ENDPOINTS.EVENTS instead
    ADD_EVENT: '/calendar/events/', // Use CALENDAR_ENDPOINTS.EVENTS instead
  },
};

// Manager Endpoints (Security: /api/man/)
export const MANAGER_ENDPOINTS = {
  APPOINTMENTS: {
    LIST: '/man/appointments/',
    CREATE: '/man/appointments/',
    UPDATE: (id: string | number) => `/man/appointments/${id}/`,
    DELETE: (id: string | number) => `/man/appointments/${id}/`,
  },
  STAFF: {
    LIST: '/man/staff/',
    UPDATE: (id: string | number) => `/man/staff/${id}/`,
  },
  CUSTOMERS: {
    LIST: '/man/customers/',
    DETAIL: (id: string | number) => `/man/customers/${id}/`,
    UPDATE: (id: string | number) => `/man/customers/${id}/`,
  },
  REPORTS: {
    REVENUE: '/man/reports/revenue/',
    APPOINTMENTS: '/man/reports/appointments/',
  },
  CALENDAR: {
    CONNECT: '/man/calendar/connect/',
    STATUS: '/man/calendar/status/',
    SYNC: '/man/calendar/sync/',
    DISCONNECT: '/man/calendar/disconnect/',
    EVENTS: '/man/calendar/events/',
    ADD_EVENT: '/man/calendar/add-event/',
  },
};

// Admin Endpoints (Security: /api/ad/)
export const ADMIN_ENDPOINTS = {
  APPOINTMENTS: {
    LIST: '/ad/appointments/',
    CREATE: '/ad/appointments/',
    DETAIL: (id: string | number) => `/ad/appointments/${id}/`,
    UPDATE: (id: string | number) => `/ad/appointments/${id}/`,
    DELETE: (id: string | number) => `/ad/appointments/${id}/`,
  },
  STAFF: {
    LIST: '/ad/staff/',
    CREATE: '/ad/staff/',
    UPDATE: (id: string | number) => `/ad/staff/${id}/`,
    DELETE: (id: string | number) => `/ad/staff/${id}/`,
    PERFORMANCE: (id: string | number) => `/ad/staff/${id}/performance/`,
    AREAS: {
      LIST: (staffId?: string | number) => staffId ? `/ad/staff-areas/?staff_id=${staffId}` : '/ad/staff-areas/',
      CREATE: '/ad/staff-areas/',
      UPDATE: (id: string | number) => `/ad/staff-areas/${id}/`,
      DELETE: (id: string | number) => `/ad/staff-areas/${id}/`,
    },
    SCHEDULES: {
      LIST: (staffId?: string | number) => staffId ? `/ad/staff-schedules/?staff_id=${staffId}` : '/ad/staff-schedules/',
      CREATE: '/ad/staff-schedules/',
      UPDATE: (id: string | number) => `/ad/staff-schedules/${id}/`,
      DELETE: (id: string | number) => `/ad/staff-schedules/${id}/`,
    },
    SERVICES: {
      LIST: (staffId?: string | number) => staffId ? `/ad/staff-services/?staff_id=${staffId}` : '/ad/staff-services/',
      CREATE: '/ad/staff-services/',
      UPDATE: (id: string | number) => `/ad/staff-services/${id}/`,
      DELETE: (id: string | number) => `/ad/staff-services/${id}/`,
    },
  },
  CUSTOMERS: {
    LIST: '/ad/customers/',
    CREATE: '/ad/customers/',
    DETAIL: (id: string | number) => `/ad/customers/${id}/`,
    UPDATE: (id: string | number) => `/ad/customers/${id}/`,
    DELETE: (id: string | number) => `/ad/customers/${id}/`,
    BOOKINGS: (id: string | number) => `/ad/customers/${id}/bookings/`,
    PAYMENTS: (id: string | number) => `/ad/customers/${id}/payments/`,
  },
  USERS: {
    LIST: '/ad/users/',
    DETAIL: (id: string | number) => `/ad/users/${id}/`,
    UPDATE: (id: string | number) => `/ad/users/${id}/`,
    DELETE: (id: string | number) => `/ad/users/${id}/`,
  },
  MANAGERS: {
    LIST: '/ad/managers/',
    CREATE: '/ad/managers/',
    UPDATE: (id: string | number) => `/ad/managers/${id}/`,
    DELETE: (id: string | number) => `/ad/managers/${id}/`,
    PERMISSIONS: (id: string | number) => `/ad/managers/${id}/permissions/`,
  },
  SERVICES: {
    LIST: '/ad/services/',
    CREATE: '/ad/services/',
    UPDATE: (id: string | number) => `/ad/services/${id}/`,
    DELETE: (id: string | number) => `/ad/services/${id}/`,
    REORDER: '/ad/services/reorder/',
    APPROVE: (id: string | number) => `/ad/services/${id}/approve/`,
  },
  CATEGORIES: {
    LIST: '/ad/categories/',
    CREATE: '/ad/categories/',
    UPDATE: (id: string | number) => `/ad/categories/${id}/`,
    DELETE: (id: string | number) => `/ad/categories/${id}/`,
    REORDER: '/ad/categories/reorder/',
  },
  SUBSCRIPTIONS: {
    LIST: '/ad/subscriptions/',
    DETAIL: (id: string | number) => `/ad/subscriptions/${id}/`,
    UPDATE: (id: string | number) => `/ad/subscriptions/${id}/`,
    CANCEL: (id: string | number) => `/ad/subscriptions/${id}/cancel/`,
    APPOINTMENTS: (id: string | number) => `/ad/subscriptions/${id}/appointments/`,
  },
  ORDERS: {
    LIST: '/ad/orders/',
    DETAIL: (id: string | number) => `/ad/orders/${id}/`,
    UPDATE: (id: string | number) => `/ad/orders/${id}/`,
    DELETE: (id: string | number) => `/ad/orders/${id}/`,
    SEND_REMINDER: (id: string | number) => `/ad/orders/${id}/send-reminder/`,
    APPROVE_CHANGE: (id: string | number) => `/ad/orders/${id}/approve-change/`,
    CANCEL: (id: string | number) => `/ad/orders/${id}/cancel/`,
    ITEMS: (id: string | number) => `/ad/orders/${id}/items/`,
  },
  REPORTS: {
    REVENUE: '/ad/reports/revenue/',
    DASHBOARD: '/ad/reports/dashboard/',
    APPOINTMENTS: '/ad/reports/appointments/',
    STAFF_PERFORMANCE: '/ad/reports/staff-performance/',
    SUBSCRIPTIONS: '/ad/reports/subscriptions/',
    ORDERS: '/ad/reports/orders/',
  },
  ROUTES: {
    OPTIMIZE: '/ad/routes/optimize/',
    STAFF_DAY: '/ad/routes/staff-day/',
  },
  COUPONS: {
    LIST: '/ad/coupons/',
    CREATE: '/ad/coupons/',
    DETAIL: (id: string | number) => `/ad/coupons/${id}/`,
    UPDATE: (id: string | number) => `/ad/coupons/${id}/`,
    DELETE: (id: string | number) => `/ad/coupons/${id}/`,
    USAGES: '/ad/coupons/usages/',
  },
  CALENDAR: {
    CONNECT: '/calendar/google/connect/',
    STATUS: '/calendar/status/',
    SYNC: '/calendar/sync/',
    DISCONNECT: '/calendar/google/disconnect/',
    EVENTS: '/calendar/events/',
    ADD_EVENT: '/calendar/events/',
    OUTLOOK_CONNECT: '/calendar/outlook/connect/',
    OUTLOOK_DISCONNECT: '/calendar/outlook/disconnect/',
    SYNC_BULK: '/calendar/sync-bulk/',
  },
};

// Shared calendar API (same for all roles: /api/calendar/)
export const CALENDAR_ENDPOINTS = {
  STATUS: '/calendar/status/',
  SYNC: '/calendar/sync/',
  SYNC_BULK: '/calendar/sync-bulk/',
  EVENTS: '/calendar/events/',
  GOOGLE_CONNECT: '/calendar/google/connect/',
  GOOGLE_DISCONNECT: '/calendar/google/disconnect/',
  OUTLOOK_CONNECT: '/calendar/outlook/connect/',
  OUTLOOK_DISCONNECT: '/calendar/outlook/disconnect/',
  ICS: (appointmentId: number) => `/calendar/ics/${appointmentId}/`,
};

// Admin endpoints for staff appointments
export const ADMIN_STAFF_ENDPOINTS = {
  APPOINTMENTS: (staffId: number) => `/ad/appointments/?staff_id=${staffId}`,
};
