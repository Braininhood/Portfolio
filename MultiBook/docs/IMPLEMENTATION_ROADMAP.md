# MultiBook Booking System - Detailed Implementation Roadmap

## Overview

This document provides a **step-by-step implementation guide** for building the MultiBook booking system. Each phase includes detailed tasks, acceptance criteria, and deliverables.

### Supabase (current stack)

**MultiBook now uses Supabase.** Keep this in mind across the roadmap:

| Supabase service | Use in MultiBook |
|-----------------|-----------------|
| **Database** | PostgreSQL hosted on Supabase. Django connects via `DATABASE_URL`. All app tables (users, orders, appointments, etc.) live here. |
| **Auth (optional)** | Supabase Auth for sign-in/sign-up; Google OAuth enabled in Dashboard. Frontend: `lib/supabase/client.ts`, `useSupabaseAuth`. |
| **Storage (optional)** | File uploads (e.g. avatars, service images) can use Supabase Storage; backend: `apps.core.supabase_storage`. |
| **Edge Functions (optional)** | Serverless tasks (e.g. webhooks, calendar sync) without running everything in Django/Celery. |

- **Setup:** See **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** for database connection, migrations, RLS, seed data, and env vars.
- **Reuse where it fits:** OAuth (Google/Microsoft) for Auth and calendar, DB for all state, Storage for files, Edge Functions for background jobs.

---

## Phase 1: Foundation & Setup (Weeks 1-3)

### Week 1: Project Setup & Architecture

#### Day 1-2: Backend Setup
**Tasks:**
- [ ] Initialize Django project with proper structure
- [ ] Set up database: **Supabase PostgreSQL** (primary; see [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)); SQLite optional for local-only dev
- [ ] Configure environment variables (.env): `DATABASE_URL`, Supabase vars (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, etc.)
- [ ] Set up Django REST Framework
- [ ] Configure CORS settings (for localhost:3000 and frontend origin)
- [ ] Set up logging and error handling
- [ ] Initialize Git repository
- [ ] Configure development settings (localhost:8000)

**Deliverables:**
- Working Django project
- **Supabase** (or local) database connection established
- Basic API structure
- Development server running on localhost:8000

#### Day 3-4: Frontend Setup
**Tasks:**
- [ ] Initialize Next.js project (App Router)
- [ ] Configure TypeScript
- [ ] Set up Tailwind CSS
- [ ] Install shadcn/ui components
- [ ] Set up API client (axios/fetch) - pointing to localhost:8000
- [ ] Configure environment variables (.env.local)
- [ ] Set up routing structure
- [ ] Configure development server (localhost:3000)

**Deliverables:**
- Working Next.js project
- Basic UI components
- API integration setup
- Development server running on localhost:3000

#### Day 5: Database Models
**Tasks:**
- [ ] Create User and Profile models (with role: admin, manager, staff, customer)
- [ ] Add calendar sync fields to Profile model (calendar_provider, tokens, settings)
- [ ] Create Manager model (with permissions configuration)
- [ ] Create Service and Category models
- [ ] Create Staff and StaffSchedule models
- [ ] Create StaffArea model (postcode, radius_km)
- [ ] Create Customer model
- [ ] Create Appointment and CustomerAppointment models
- [ ] Add calendar_event_id (JSON) and calendar_synced_to (JSON) to Appointment
- [ ] Create initial migrations
- [ ] Run migrations against **Supabase PostgreSQL** (see [SUPABASE_SETUP.md](./SUPABASE_SETUP.md))
- [ ] Create admin superuser

**Deliverables:**
- Complete database schema (**Supabase** PostgreSQL)
- Django admin access
- Sample data capability
- Manager role support

**Acceptance Criteria:**
- All models created and migrated (Supabase DB)
- Admin panel accessible at localhost:8000/admin
- Can create sample data via admin
- Manager model with permission fields

---

### Week 2: Authentication & Core API

#### Day 1-2: Authentication System
**Tasks:**
- [ ] Implement JWT authentication (Django and/or **Supabase Auth**; see [SUPABASE_SETUP.md](./SUPABASE_SETUP.md))
- [ ] Create login endpoint
- [ ] Create register endpoint
- [ ] Create password reset flow
- [ ] Create email verification
- [ ] **Optional:** Use Supabase Auth + OAuth (Google, etc.) in Dashboard → Authentication → Providers
- [ ] Implement role-based permissions (Admin, Manager, Staff, Customer)
- [ ] Create manager permission system
- [ ] Create authentication middleware
- [ ] Role-based access control decorators

**Deliverables:**
- Working authentication API
- JWT token generation (or Supabase sessions)
- Role-based access control (4 roles)
- Manager permission system

#### Day 3-4: Core API Endpoints
**Tasks:**
- [x] Services API (list, detail)
- [x] Staff API (list, detail)
- [x] Customer API (CRUD)
- [x] Appointment API (CRUD)
- [x] API documentation (Swagger/OpenAPI)
- [x] API versioning
- [x] Error handling

**Deliverables:**
- Complete REST API ✅
- API documentation ✅
- Error responses standardized ✅

#### Day 5: Frontend Authentication
**Tasks:**
- [x] Create login page
- [x] Create register page
- [x] Implement auth context/hooks
- [x] Create protected routes (customer, staff, manager, admin)
- [x] Implement token storage
- [x] Create logout functionality
- [x] Role-based route protection
- [x] Role-based UI rendering

**Deliverables:**
- Working authentication UI ✅
- Protected routes (4 role types) ✅
- User session management ✅
- Role-based navigation ✅

**Acceptance Criteria:**
- Users can register and login ✅
- Protected routes work correctly for all roles ✅
- JWT tokens stored securely ✅
- Role-based UI rendering (customer, staff, manager, admin) ✅
- Manager sees only assigned scope ✅

---

### Week 3: Basic Booking Flow

#### Day 1-2: Booking Step 1 - Postcode Entry
**Tasks:**
- [ ] Create postcode input component
- [ ] Postcode validation (UK format)
- [ ] API endpoint: Get services by postcode
- [ ] API endpoint: Get staff by postcode/area
- [ ] Postcode-to-area mapping logic
- [ ] Service filtering by area
- [ ] Navigation to service selection

**Deliverables:**
- Postcode entry UI
- Postcode validation
- Area-based service filtering
- State management for postcode

#### Day 3-4: Booking Step 2 - Service Selection (Area-Based)
**Tasks:**
- [ ] Create service listing page (filtered by postcode area)
- [ ] Service card component
- [ ] Service detail modal/page
- [ ] Show available staff in area
- [ ] Service selection state management
- [ ] Navigation to next step

**Deliverables:**
- Area-based service selection UI
- Service details display
- Staff availability by area
- State management for booking

#### Day 5: Booking Step 3 - Date & Time Selection
**Tasks:**
- [ ] Create calendar component
- [ ] Implement time slot calculation logic
- [ ] Create available slots API endpoint
- [ ] Time slot selection UI
- [ ] Date/time validation
- [ ] Navigation between steps

**Deliverables:**
- Calendar picker
- Time slot selection
- Available slots API

#### Day 5: Booking Step 4 - Guest Details & Payment (NO LOGIN REQUIRED)
**Tasks:**
- [ ] Create guest customer details form (name, email, phone, address)
- [ ] **Guest checkout support** - No login/registration required
- [ ] Google Places API integration for address autocomplete
- [ ] Address auto-fill from postcode
- [ ] Form validation
- [ ] Create payment page (basic) - Works for guests
- [ ] Booking confirmation page - Guest order confirmation
- [ ] Generate order number and tracking token for guest orders
- [ ] Session management for booking
- [ ] Complete guest checkout flow

**Deliverables:**
- Complete guest checkout flow (postcode-first, no login required)
- Google Places address autocomplete
- Form validation
- Guest booking confirmation
- Order number and tracking token generation

**Acceptance Criteria:**
- Postcode-first booking flow works end-to-end
- Services filtered by postcode area
- Staff filtered by postcode area
- Google Places autocomplete works
- Data persists between steps
- **Guest checkout works without login/registration**
- **Guest order creates appointment in database (customer FK nullable)**
- **Guest receives confirmation with order number and tracking link**
- **Perfect for elderly customers who don't want to register**

#### Day 6: Post-Order Account Linking 
**Tasks:**
- [x] Implement email checking API endpoint (`/api/bkg/guest/check-email/`)
- [x] Create account linking prompt UI (after order completion)
- [x] Login modal for existing account linking
- [x] Registration modal for new account creation (pre-filled details)
- [x] "Skip" option for customers who don't want to register
- [x] Account linking API endpoints:
  - `/api/bkg/guest/order/{order_number}/link-login/`
  - `/api/bkg/guest/order/{order_number}/link-register/`
- [x] Guest order linking logic (update customer FK when linked)

**Deliverables:**
- Post-order account linking flow
- Login modal for account linking
- Registration modal with pre-filled details
- "Skip" option (elderly-friendly)
- Account linking API endpoints

**Acceptance Criteria:**
- System checks if customer email exists after order completion
- If email exists: Show login prompt to link order to account
- If email doesn't exist: Show registration prompt (optional)
- Customer can skip account linking - guest order continues to work
- Guest order can be linked to account later (via login or registration)
- **Guest orders work perfectly even if customer doesn't register**
- **Perfect for elderly customers who prefer not to register**

---

## Phase 2: Enhanced Features (Weeks 4-5)

### Week 4: Payment Integration & Calendar Sync

#### Day 1-2: Stripe Integration -*Temporarily unavailable – waiting for customer access.*
**Tasks:**
- [ ] Install Stripe SDK
- [ ] Create payment intent endpoint
- [ ] Create payment confirmation endpoint
- [ ] Create webhook handler
- [ ] Payment status tracking
- [ ] Error handling for payments

**Deliverables:**
- Stripe payment integration 
- Payment processing
- Webhook handling

#### Day 3: PayPal Integration - *Temporarily unavailable – waiting for customer access.*
**Tasks:**
- [ ] Install PayPal SDK
- [ ] Create PayPal order endpoint
- [ ] Create PayPal capture endpoint
- [ ] Payment status tracking
- [ ] Error handling

**Deliverables:**
- PayPal payment integration
- Multiple payment options

#### Day 4-5: Multi-Calendar Integration (All Roles)

**Note: We now work with Supabase.** Use Supabase where it fits to avoid duplicating work:
- **Supabase Auth → OAuth (callback URL):**  
  **Callback URL (for OAuth):** `https://[PROJECT_REF].supabase.co/auth/v1/callback`  
  Example: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`  
  Configure this in [Supabase Dashboard](https://supabase.com/dashboard) → Authentication → URL Configuration, and in each provider (Google, etc.) as the redirect URI.
- **Supabase Auth → OAuth providers:** Enable Google in Dashboard → Authentication → Providers. **Microsoft (Azure AD / Outlook):** *Temporarily unavailable – waiting for customer access.* Reuse Google OAuth for calendar where possible (e.g. same token for Auth + Calendar scope).
- **Supabase Database:** Calendar connection state (tokens, refresh tokens, provider, user link) lives in our Django models/tables already in Supabase (e.g. `calendar_sync` or profile-related tables).
- **Supabase Edge Functions** (optional): For serverless calendar sync (e.g. webhook handlers, background sync) if we don’t want to run everything in Django/Celery.
- **Supabase Storage** (optional): Store .ics files or export artifacts if needed.

**Tasks:**
- [ ] Set up Google Calendar API (use Supabase Google OAuth; callback URL above)
- [ ] Microsoft Graph API (Outlook): *Paused until customer provides access*
- [ ] Set up Apple Calendar (iCal/CalDAV)
- [ ] OAuth 2.0 flow for Google (Supabase callback); Outlook when available
- [ ] Calendar sync in Profile model (all users); store tokens/state in Supabase DB
- [ ] Calendar connection UI for all roles
- [ ] Create calendar event on booking (auto-sync)
- [ ] Update calendar event on changes
- [ ] Delete calendar event on cancellation
- [ ] Add custom events to external calendars (all roles)
- [ ] **Order confirmation page: "Add booking to calendar"** (download .ics, Add to Google Calendar)
- [ ] Two-way sync (optional)
- [ ] Calendar sync status dashboard
- [ ] Bulk sync operations (admin)
- [ ] Download .ics files

**Deliverables:**
- Google Calendar sync (all roles)
- Outlook Calendar sync (all roles) – *when customer access is provided*
- Apple Calendar support (all roles)
- Custom event creation (all roles)
- **Add to calendar on confirmation page (.ics + Google Calendar)**
- Calendar sync management UI
- OAuth flow for Google (Supabase callback); Microsoft when available

**Acceptance Criteria:**
- Payments process successfully
- **Customer can add booking to calendar from order confirmation page**
- Calendar events created automatically for all roles
- Staff can sync schedule to personal calendar
- Customer can sync appointments to personal calendar
- Manager can sync appointments to personal calendar
- Admin can sync all appointments to personal calendar
- All roles can add custom events to external calendars
- Webhooks handle payment status
- OAuth flow works smoothly for Google (Supabase); Microsoft when available

---

### Week 5: Address Integration & Notifications

#### Day 1-2: Google Places API Integration
**Tasks:**
- [x] Set up Google Places API
- [x] Get Google API key
- [x] Create address autocomplete endpoint
- [x] Implement Google Places Autocomplete widget
- [x] Address form population on selection
- [x] Postcode extraction from address
- [x] Manual address entry fallback
- [x] Address validation

**Deliverables:**
- Google Places address autocomplete
- Address validation
- Form integration
- Postcode extraction

**Verification (double-checked):**
- **Backend:** `GET /api/addr/autocomplete/?query=...` and `GET|POST /api/addr/validate/?place_id=...` or `?postcode=...` (see `backend/apps/core/views_address.py`, `backend/apps/core/address.py`). UK-only (`country:gb`). Requires `GOOGLE_MAPS_API_KEY` or `GOOGLE_PLACES_API_KEY` in `backend/.env`; enable **Places API** and **Geocoding API** in Google Cloud.
- **Frontend:** Booking details page (`frontend/app/booking/details/page.tsx`) uses autocomplete → on select calls validate with `place_id` → populates address line1, line2, city, postcode, country. Manual fields and fallback if no results or API key missing.
- **Flow:** Type address/postcode → suggestions from backend → select → validate returns full address → form filled; user can edit. Without API key, autocomplete returns empty and user can enter address manually.

#### Day 3-4: Email Notifications (Google Gmail + Supabase)

**Stack:** **Google Gmail SMTP** for sending (Django); optional **Supabase Edge Functions** or **pg_cron** for reminder cron. Configure in `backend/.env`: `EMAIL_HOST=smtp.gmail.com`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (use [Google App Password](https://support.google.com/accounts/answer/185833)), `DEFAULT_FROM_EMAIL`. See `backend/.env.example`.

**Tasks:**
- [x] Set up email service: **Google Gmail SMTP** (Django); optional Supabase Edge Functions for queue
- [x] Create email templates (`backend/templates/emails/`: `booking_confirmation`, `booking_reminder`, `booking_cancellation` .html + .txt)
- [x] Booking confirmation email (sent on order confirm via `apps/notifications/email_service.send_booking_confirmation` and order signals/views)
- [x] Reminder email (template + `send_booking_reminder`; run daily via `python manage.py send_booking_reminders` or cron / Supabase pg_cron)
- [x] Cancellation email (sent when order is cancelled – customer and guest cancel endpoints)
- [x] Reminder job: management command `send_booking_reminders` (optional: Celery beat or Supabase Edge Function / pg_cron to run daily)

**Deliverables:**
- [x] Email notification system (Google Gmail SMTP)
- [x] Email templates (confirmation, reminder, cancellation)
- [x] Automated emails (confirmation on book; cancellation on cancel; reminders via cron/command)

#### Day 5: SMS Notifications *Temporarily unavailable – waiting for customer access.*
**Tasks:**
- [ ] Set up Twilio
- [ ] Create SMS service
- [ ] Booking confirmation SMS
- [ ] Reminder SMS
- [ ] SMS queue (Celery)

**Deliverables:**
- SMS notification system
- Automated SMS

**Acceptance Criteria:**
- Address autocomplete works
- Emails send successfully
- SMS notifications work
- Templates are customizable

---

## Phase 3: Management Tools (Weeks 6-8)

### Week 6: Admin Dashboard

#### Day 1-2: Dashboard Overview
**Tasks:**
- [x] Create admin dashboard layout (`/ad/dashboard` with `DashboardLayout`)
- [x] Key metrics widgets (orders today/week, appointments today, revenue today/month, customers, staff, pending change requests)
- [x] Recent activity feed (recent orders + upcoming appointments; links to `/ad/orders` and order detail)
- [x] Quick actions panel (New booking, Customers, Orders, Revenue report, Staff, Services)
- [x] Auto-refresh every 60s (lightweight “real-time”; WebSocket optional for later)

**Deliverables:**
- [x] Admin dashboard (`frontend/app/ad/dashboard/page.tsx`)
- [x] Metrics display (API: `GET /api/ad/reports/dashboard/` – `backend/apps/reports/views.dashboard_overview_view`)
- [x] Quick actions + recent orders + upcoming appointments
- [x] Admin orders list and detail (`/ad/orders`, `/ad/orders/[id]`) for dashboard links

#### Day 3-4: Calendar Management
**Tasks:**
- [ ] Advanced calendar component
- [ ] Monthly/Weekly/Daily views
- [ ] Drag-and-drop functionality
- [ ] Appointment editing
- [ ] Bulk operations
- [ ] Filter and search

**Deliverables:**
- Advanced calendar view
- Drag-and-drop editing
- Filtering capabilities

#### Day 5: Appointment Management
**Tasks:**
- [ ] Appointment list view
- [ ] Appointment detail modal
- [ ] Status management
- [ ] Bulk actions
- [ ] Export functionality
- [ ] Search and filters

**Deliverables:**
- Appointment management UI
- Status updates
- Export features

**Acceptance Criteria:**
- Dashboard displays accurate metrics
- Calendar editing works smoothly
- Appointments can be managed efficiently

---

### Week 7: Staff & Customer Management

#### Day 1-2: Staff Management
**Tasks:**
- [x] **Backend: Staff models & API** ✅
  - [x] Staff, StaffSchedule, StaffService, StaffArea models
  - [x] StaffViewSet, StaffAreaViewSet, StaffScheduleViewSet, StaffServiceViewSet
  - [x] Postcode utilities (distance calculation, get_staff_for_postcode)
  - [x] Django Admin with inlines (services, schedules, areas)
  - [x] StaffArea model with postcode + radius_km
  - [x] Multiple areas per staff (via StaffArea model)
  - [x] Postcode-to-area distance calculation (Haversine formula)
- [x] **Frontend: Staff list view** ✅
- [x] **Frontend: Staff detail/edit pages** ✅
- [x] **Frontend: Schedule management UI** ✅
- [x] **Frontend: Service assignments UI** ✅
- [x] **Frontend: Area/Postcode Assignment Interface** ✅
  - [x] Postcode assignment interface
  - [x] Radius configuration (km)
  - [x] Multiple areas per staff (UI)
  - [x] Area coverage map visualization (Google Maps) ✅
- [x] **Frontend: Performance metrics** ✅
  - [x] Jobs completed, revenue, completion rate
  - [x] Response time, no-show rate
  - [x] Services breakdown
  - [x] Period filters (7/30/90 days)
- [x] **Frontend: Calendar integration per staff** ✅
  - [x] Calendar status display
  - [x] Google Calendar integration status
  - [x] Outlook integration status
  - [x] Apple Calendar info (.ics download)

**Deliverables:**
- ✅ Backend: Staff management system (API complete)
- ✅ Backend: Area/postcode assignment system (models & logic complete)
- ✅ Frontend: Staff management UI (complete)
- ✅ Frontend: Schedule editor (complete)
- ✅ Frontend: Area/postcode assignment UI (complete)
- ✅ Frontend: Performance tracking (complete)
- ✅ Frontend: Calendar integration per staff (complete)

**Status:** ✅ **100% COMPLETE** - All Week 7, Day 1-2 tasks implemented!
**See:** `PERFORMANCE_AND_CALENDAR_IMPLEMENTATION.md` for full details.

**Status:** ✅ **COMPLETE** - All core functionality implemented!
**See:** `STAFF_MANAGEMENT_IMPLEMENTATION_COMPLETE.md` for full details.

#### Day 3-4: Customer Management
**Tasks:**
- [x] Customer list view ✅
- [x] Customer detail pages ✅
- [x] Booking history ✅
- [x] Payment history ✅
- [x] Notes and tags ✅
- [x] Search and filters ✅

**Deliverables:**
- ✅ Customer management system
- ✅ History tracking
- ✅ Search capabilities

**Status:** ✅ **100% COMPLETE** - All Week 7, Day 3-4 tasks implemented!
**See:** `CUSTOMER_MANAGEMENT_IMPLEMENTATION.md` for full details.

#### Day 5: Service Management
**Tasks:**
- [x] Service list view ✅
- [x] Service create/edit forms ✅
- [x] Category management ✅
- [x] Pricing management ✅
- [x] Staff assignments ✅
- [x] Drag-and-drop ordering ✅

**Deliverables:**
- ✅ Service management system
- ✅ Category organization
- ✅ Pricing controls

**Acceptance Criteria:**
- ✅ All management interfaces work
- ✅ Data can be created/updated/deleted
- ✅ Search and filters function properly

**Status:** ✅ **100% COMPLETE** - All Week 7, Day 5 tasks implemented!
**See:** `SERVICE_MANAGEMENT_IMPLEMENTATION.md` for full details.

---

### Week 8: Staff & Customer Portals

#### Day 1-2: Staff Portal
**Tasks:**
- [x] Staff dashboard ✅
- [x] Today's schedule view ✅
- [x] Job list view ✅
- [x] Job detail view ✅
- [x] Check-in/Check-out ✅
- [x] Photo upload ✅
- [x] Status updates ✅

**Deliverables:**
- ✅ Staff portal
- ✅ Job management
- ✅ Mobile-responsive

**Status:** ✅ **100% COMPLETE** - All Week 8, Day 1-2 tasks implemented!
**See:** `STAFF_PORTAL_IMPLEMENTATION.md` for full details.

#### Day 3-4: Customer Portal
**Tasks:**
- [x] Customer dashboard ✅
- [x] Upcoming appointments ✅
- [x] Past appointments ✅
- [x] Appointment detail view ✅
- [x] Cancel/reschedule functionality ✅
- [x] Payment history ✅
- [x] Profile management ✅

**Deliverables:**
- ✅ Customer portal
- ✅ Self-service features
- ✅ Profile management

**Status:** ✅ **100% COMPLETE** - All Week 8, Day 3-4 tasks implemented!
**See:** `CUSTOMER_PORTAL_IMPLEMENTATION.md` for full details.

#### Day 5: Mobile Optimization
**Tasks:**
- [x] Responsive design testing ✅
- [x] Mobile navigation ✅
- [x] Touch-friendly interactions ✅
- [x] Mobile form optimization ✅
- [x] PWA setup ✅

**Deliverables:**
- ✅ Mobile-optimized UI
- ✅ Touch interactions
- ✅ Responsive layouts

**Acceptance Criteria:**
- ✅ Portals work on all devices
- ✅ Mobile experience is smooth
- ✅ All features accessible on mobile

**Status:** ✅ **100% COMPLETE** - All Week 8, Day 5 tasks implemented!
**See:** `MOBILE_OPTIMIZATION_IMPLEMENTATION.md` for full details.

---

## Phase 4: Advanced Features (Weeks 9-11)

### Week 9: Subscriptions & Orders (Guest Checkout Support)

**Note: All subscription and order features support guest checkout - no login/registration required.**

#### Day 1-2: Subscription System (Guest Checkout Support)
**Tasks:**
- [x] Subscription model (frequency, duration, etc.) ✅
  - [x] `customer` FK (nullable for guest subscriptions) ✅
  - [x] `guest_email`, `guest_name`, `guest_phone` (for guest subscriptions) ✅
  - [x] `subscription_number` (unique identifier) ✅
  - [x] `tracking_token` (for guest access via email link) ✅
  - [x] `is_guest_subscription` flag ✅
  - [x] `account_linked_at` timestamp ✅
- [x] SubscriptionAppointment model ✅
- [x] Subscription creation logic (supports guest checkout) ✅
- [x] Automatic appointment generation from subscriptions ✅
- [x] Subscription schedule calculation ✅
- [ ] UI for subscription selection (weekly/biweekly/monthly, 1-12 months)
- [ ] Subscription preview
- [x] Staff schedule showing subscription appointments ✅
- [x] 24h cancellation policy for subscription appointments ✅
- [x] Guest subscription access endpoints (no auth required) ✅

**Deliverables:**
- ✅ Subscription system
- ✅ Automatic appointment generation (intelligent scheduling - checks staff availability, moves to next day if needed)
- ✅ Subscription management (backend)
- ✅ Staff schedule integration

**Status:** ✅ **95% COMPLETE** - Backend fully implemented! Frontend UI pending.
**See:** `SUBSCRIPTION_SYSTEM_IMPLEMENTATION.md` for full details.

#### Day 3-4: Order System (Multi-Service, Guest Checkout Support)
**Tasks:**
- [x] Order model ✅
  - [x] `customer` FK (nullable for guest orders) ✅
  - [x] `guest_email`, `guest_name`, `guest_phone` (for guest orders) ✅
  - [x] `order_number` (unique identifier) ✅
  - [x] `tracking_token` (for guest access via email link) ✅
  - [x] `is_guest_order` flag ✅
  - [x] `account_linked_at` timestamp ✅
  - [x] Guest address fields (address_line1, city, postcode, etc.) ✅
- [x] OrderItem model ✅
- [x] Multi-service order creation (supports guest checkout - NO AUTH REQUIRED) ✅
- [x] Order status management ✅
- [x] Order scheduling logic ✅
- [ ] UI for adding multiple services to order (guest-friendly)
- [x] Order summary and pricing ✅
- [x] Staff assignment for order items ✅
- [x] 24h cancellation policy for orders ✅
- [x] Order change request system ✅
- [x] Guest order access endpoints (no auth required) ✅
- [x] Guest order tracking by order number + email ✅

**Deliverables:**
- ✅ Order system
- ✅ Multi-service booking
- ✅ Order management
- ✅ Change request workflow

**Status:** ✅ **95% COMPLETE** - Backend fully implemented! Frontend UI for multi-service selection pending.
**See:** `ORDER_SYSTEM_IMPLEMENTATION.md` for full details.

#### Day 3-4: Coupon System
**Tasks:**
- [x] Coupon model ✅
- [x] Coupon validation logic ✅
- [x] Coupon application UI ✅
- [x] Usage tracking ✅
- [x] Expiry management ✅
- [x] Service restrictions ✅

**Deliverables:**
- ✅ Coupon system
- ✅ Discount application
- ✅ Usage tracking

**Status:** ✅ **100% COMPLETE** - All Week 9, Day 3-4 tasks implemented!
**See:** `COUPON_SYSTEM_IMPLEMENTATION.md` for full details.

#### Day 5: Order Management & Cancellation Policies (Guest Support)
**Tasks:**
- [x] Order change request UI (customer and guest) ✅
- [x] Guest order change request (via email link or order number lookup) ✅
- [x] Order change approval workflow (admin) ✅
- [x] Cancellation policy enforcement (24h before) ✅
- [x] Subscription appointment cancellation (24h before) ✅
- [x] Order cancellation (24h before scheduled date) ✅
  - [x] Guest order cancellation (via email link or order number) ✅
- [x] Cancellation deadline calculation ✅
- [x] Can_cancel/can_reschedule flags ✅
- [x] Customer order management interface (if account linked) ✅
- [x] Guest order management interface (via email link/tracking token) ✅
- [x] Order status tracking (works for both guest and account-linked orders) ✅
- [x] Guest order tracking page (no login required) ✅

**Deliverables:**
- Order management system
- Cancellation policy enforcement
- Change request workflow
- Customer order interface

**Acceptance Criteria:**
- Subscriptions create appointments automatically
- Subscription appointments show in staff schedule
- Orders can contain multiple services
- **Guest checkout works for subscriptions and orders (NO LOGIN REQUIRED)**
- **Guest orders work perfectly even if customer doesn't register**
- **Perfect for elderly customers who don't want to create accounts**
- Order change requests work correctly (for both guest and account-linked orders)
- 24h cancellation policy enforced
- Customers can manage subscriptions and orders (if account linked)
- Guest customers can manage orders via email link/order number (no account needed)

---

### Week 10: Reporting & Analytics

#### Day 1-2: Revenue Reports
**Tasks:**
- [x] Revenue calculation logic ✅
- [x] Revenue by period (day/week/month) ✅
- [x] Revenue by service ✅
- [x] Revenue by staff ✅
- [x] Revenue charts/graphs ✅
- [x] Export to CSV ✅
- [x] Export to PDF (requires reportlab library - documented) ✅

**Deliverables:**
- Revenue reporting
- Visualizations
- Export functionality

#### Day 3-4: Appointment Reports
**Tasks:**
- [x] Appointment statistics
- [x] Booking trends
- [x] Popular services
- [x] Peak times analysis
- [x] Cancellation rates
- [x] Conversion metrics

**Deliverables:**
- Appointment analytics (`GET /api/ad/reports/appointments/`; frontend: `/ad/reports/appointments`)
- Trend analysis (booking_trends by day; peak_times by hour and day of week)
- Performance metrics (cancellation_rates, conversion_metrics, popular_services)

#### Day 5: Staff Performance Reports
**Tasks:**
- [x] Jobs completed
- [x] Customer ratings (placeholder: avg_rating/rating_count in API; no rating model yet)
- [x] Utilization rate
- [x] Revenue per staff
- [x] Performance comparisons

**Deliverables:**
- Staff performance tracking (`GET /api/ad/reports/staff-performance/`; frontend: `/ad/reports/staff-performance`)
- Comparative analytics (rank by jobs, revenue, utilization)
- Performance dashboards (summary + per-staff table)

**Acceptance Criteria:**
- Reports generate accurately
- Data visualizations are clear
- Export functions work
- Performance metrics are meaningful

---

### Week 11: Route Optimization & Advanced Calendar

#### Day 1-2: Route Optimization
**Tasks:**
- [x] Google Maps integration (Geocoding + Distance Matrix API; map on frontend via NEXT_PUBLIC_GOOGLE_MAPS_API_KEY)
- [x] Distance calculation (Distance Matrix API in `backend/apps/core/route_utils.py`)
- [x] Route optimization algorithm (greedy nearest-neighbour in `route_utils.optimize_route_greedy`)
- [x] Multi-stop routing (POST `/api/ad/routes/optimize/`; GET `/api/ad/routes/staff-day/` for staff+date)
- [x] Route visualization (markers + polyline on map at `/ad/routes`)
- [x] Estimated travel time (per-leg and total in response; displayed on page)

**Deliverables:**
- Route optimization (`/ad/routes`: load staff day → edit stops → optimize → ordered list + map)
- Map visualization (Google Maps with numbered markers and polyline for optimized order)
- Travel time estimates (leg minutes and total minutes)

#### Day 3-4: Calendar Sync UI & Management
**Tasks:**
- [x] Calendar connection interface (all roles); store connection state in **Django models** (Profile)
- [x] Calendar sync settings page (`/settings/calendar` for all roles)
- [x] Sync status indicators (last_sync_at, last_sync_error in status + UI)
- [x] Manual sync trigger (POST `/api/calendar/sync/`)
- [x] Bulk sync operations (admin) (POST `/api/calendar/sync-bulk/`; UI at `/ad/settings/calendar`)
- [x] Custom event creation UI (form on settings page; POST `/api/calendar/events/`)
- [x] Calendar event management (GET `/api/calendar/events/` lists synced appointments)
- [x] Sync error handling and retry (last_sync_error stored; manual "Sync now" retry)
- [ ] **Optional:** Supabase Edge Functions for serverless sync jobs

**Deliverables:**
- Calendar sync UI for all roles
- Sync management dashboard
- Custom event creation
- Error handling

#### Day 5: Calendar Sync Testing & Optimization
**Tasks:**
- [x] Test calendar sync for all roles (backend tests in `apps/calendar_sync/tests.py`: status, manual sync, bulk sync; Staff/Customer paths covered; Admin/Manager use bulk or settings)
- [x] Test custom event creation (API validation tests: POST without start/end returns 400; GET events returns 200 with `events` array)
- [ ] Test two-way sync (if enabled) — **not in scope**: current design is one-way (MultiBook → external calendar only)
- [x] Performance optimization (sync is per-user, batch of appointments; acceptable for typical load; no N+1 in list)
- [x] Error recovery mechanisms (`last_sync_error` stored in Profile; "Sync now" retry; UI shows error; friendlier message when all events fail: "Try syncing again or reconnect your calendar")
- [ ] Sync conflict resolution — **future**: no merge of external calendar edits; conflicts not auto-resolved

**Deliverables:**
- Tested calendar sync system (`apps/calendar_sync/tests.py`)
- Optimized sync performance (per-user batch; error message on full failure)
- Error recovery (last_sync_error + retry + reconnect hint)

**Acceptance Criteria:**
- Route optimization saves time
- Calendar syncs work reliably for all roles (Staff, Customer, Manager, Admin)
- All calendar formats supported (Google, Outlook, Apple)
- Custom events can be added by all roles
- Sync errors handled gracefully

---

## Phase 5: Polish & Optimization (Weeks 12-13)

### Week 12: Performance Optimization

#### Day 1-2: Backend Optimization
**Tasks:**
- [x] **Database:** Query optimization on **Supabase PostgreSQL**; indexes already on orders, appointments, subscriptions, staff, services (see [PHASE5_OPTIMIZATION.md](./PHASE5_OPTIMIZATION.md))
- [x] Implement caching (LocMemCache in base when no REDIS_URL; Redis in production when REDIS_URL set; database cache option for Supabase-only)
- [x] API response optimization (select_related/prefetch_related used across orders, appointments, staff, customers, services)
- [ ] Background task optimization (Celery optional when REDIS_URL set)
- [ ] Load testing (locust/k6/wrk – manual)

**Deliverables:**
- Optimized backend (cache + query patterns documented in PHASE5_OPTIMIZATION.md)
- Fast API responses
- Efficient database queries (Supabase)

#### Day 3-4: Frontend Optimization
**Tasks:**
- [x] Code splitting (Next.js App Router automatic per-route)
- [ ] Image optimization (use `next/image` for images; add `images.domains` if CDN)
- [ ] Lazy loading (use `next/dynamic` for heavy client components)
- [ ] Bundle size optimization (run `@next/bundle-analyzer`; manual)
- [ ] Performance monitoring (optional: Vercel Analytics / Lighthouse CI)
- [ ] Lighthouse optimization (run against production build; target > 90)

**Deliverables:**
- Fast page loads
- Optimized bundles
- High Lighthouse scores

#### Day 5: SEO Optimization
**Tasks:**
- [x] Meta tags (root layout: title template, description; metadataBase)
- [x] Open Graph tags (openGraph in layout; siteName, title, description, locale)
- [x] Structured data (JSON-LD: Organization + WebSite on home; `frontend/lib/seo.ts`)
- [x] Sitemap generation (`app/sitemap.ts` → `/sitemap.xml`)
- [x] robots.txt (`app/robots.ts` → `/robots.txt`; allow /, disallow /api/, /auth/, dashboards; sitemap link)
- [ ] SEO testing (manual: Rich Results Test, Lighthouse SEO)

**Deliverables:**
- SEO-optimized pages (meta, OG, JSON-LD, sitemap, robots)
- Rich snippets (Organization, WebSite)
- Search engine visibility

**Acceptance Criteria:**
- Page load times < 2 seconds
- API responses < 200ms
- Lighthouse score > 90
- SEO best practices followed

---

### Week 13: Testing & Quality Assurance

#### Day 1-2: Unit Testing
**Tasks:**
- [ ] Backend unit tests
- [ ] Frontend component tests
- [ ] API endpoint tests
- [ ] Utility function tests
- [ ] Test coverage > 80%

**Deliverables:**
- Comprehensive test suite
- High test coverage
- Automated testing

#### Day 3-4: Integration Testing
**Tasks:**
- [ ] End-to-end booking flow
- [ ] Payment processing tests
- [ ] Calendar sync tests
- [ ] Notification tests
- [ ] User workflow tests

**Deliverables:**
- Integration test suite
- E2E test coverage
- Automated test runs

#### Day 5: User Acceptance Testing
**Tasks:**
- [ ] Customer journey testing
- [ ] Staff workflow testing
- [ ] Admin functionality testing
- [ ] Bug fixes
- [ ] Feedback incorporation

**Deliverables:**
- UAT completed
- Bugs fixed
- User feedback addressed

**Acceptance Criteria:**
- All tests pass
- No critical bugs
- User workflows validated
- Performance targets met

---

## Phase 6: Launch Preparation (Weeks 14-15)

### Week 14: Security & Documentation

#### Day 1-2: Security Audit
**Tasks:**
- [ ] Security vulnerability scan
- [ ] Penetration testing
- [ ] Data encryption review
- [ ] Authentication security
- [ ] API security review
- [ ] GDPR compliance check

**Deliverables:**
- Security audit report
- Vulnerabilities fixed
- Compliance verified

#### Day 3-4: Documentation
**Tasks:**
- [ ] API documentation
- [ ] User guides (customer, staff, admin)
- [ ] Developer documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Video tutorials (optional)

**Deliverables:**
- Complete documentation
- User guides
- Technical docs

#### Day 5: Training Materials
**Tasks:**
- [ ] Admin training guide
- [ ] Staff training guide
- [ ] Customer FAQ
- [ ] Video walkthroughs
- [ ] Training sessions

**Deliverables:**
- Training materials
- User support resources
- Knowledge base

**Acceptance Criteria:**
- Security issues resolved
- Documentation complete
- Training materials ready
- Users can operate system

---

### Week 15: Deployment & Launch

#### Day 1-2: Production Setup
**Tasks:**
- [ ] Production environment setup
- [ ] **Supabase:** Production project (or same project); `DATABASE_URL`, Supabase API keys, RLS and backups (see [SUPABASE_SETUP.md](./SUPABASE_SETUP.md))
- [ ] Database migration (run against Supabase)
- [ ] SSL certificates
- [ ] Domain configuration
- [ ] CDN setup
- [ ] Monitoring setup

**Deliverables:**
- Production environment
- **Supabase** DB (and optional Auth/Storage) configured for production
- Secure hosting
- Monitoring active

#### Day 3-4: Deployment
**Tasks:**
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Database migration (Supabase; env `DATABASE_URL`, Supabase keys)
- [ ] Static files collection
- [ ] Environment variables (incl. `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` if using Supabase Auth)
- [ ] Smoke testing

**Deliverables:**
- Live system
- All features working (DB/Auth/Storage on Supabase where used)
- Performance verified

#### Day 5: Launch & Monitoring
**Tasks:**
- [ ] Final testing
- [ ] User communication
- [ ] Launch announcement
- [ ] Monitor system
- [ ] Handle issues
- [ ] Collect feedback

**Deliverables:**
- System live
- Users onboarded
- Monitoring active
- Support ready

**Acceptance Criteria:**
- System is live and stable
- All features working
- Users can access system
- Support team ready
- Monitoring in place

---

## Post-Launch (Ongoing)

### Week 16+: Maintenance & Improvements

**Ongoing Tasks:**
- [ ] Bug fixes and patches
- [ ] Performance monitoring
- [ ] User feedback collection
- [ ] Feature enhancements
- [ ] Security updates
- [ ] Regular backups
- [ ] System optimization

**Monthly Reviews:**
- [ ] Performance metrics review
- [ ] User feedback analysis
- [ ] Feature requests prioritization
- [ ] Security updates
- [ ] System health check

---

## Success Criteria Summary

### Technical Success
- ✅ All features implemented and working
- ✅ Performance targets met
- ✅ Security standards met
- ✅ Test coverage > 80%
- ✅ Documentation complete

### User Success
- ✅ Booking completion rate > 80%
- ✅ Average booking time < 3 minutes
- ✅ Customer satisfaction > 4.5/5
- ✅ Staff adoption rate > 80%
- ✅ Admin efficiency improved > 50%

### Business Success
- ✅ Online booking conversion > 15%
- ✅ Payment success rate > 98%
- ✅ System uptime > 99.9%
- ✅ Revenue increase measurable
- ✅ Operational efficiency improved

---

## Risk Mitigation

### Technical Risks
- **Database (Supabase)**: Use indexing and connection pooling; monitor usage in Supabase Dashboard; RLS and backups as per [SUPABASE_SETUP.md](./SUPABASE_SETUP.md).
- **Payment Failures**: Multiple payment gateways and retry logic
- **Calendar Sync Issues**: Robust error handling and retry mechanisms
- **Third-Party API Failures**: Fallback options and graceful degradation

### Timeline Risks
- **Scope Creep**: Strict phase boundaries and change management
- **Resource Constraints**: Buffer time in each phase
- **Integration Challenges**: Early integration testing
- **Third-Party Delays**: Alternative solutions ready

### User Adoption Risks
- **Training**: Comprehensive documentation and training
- **Change Resistance**: User-friendly design and gradual rollout
- **Technical Barriers**: Simple, intuitive interface
- **Support**: Dedicated support during launch

---

*This roadmap is a living document and will be updated as the project progresses.*

**Stack:** Backend (Django), Frontend (Next.js), **Database & optional Auth/Storage (Supabase)**. See **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** for Supabase setup and configuration.

**Last Updated:** [Current Date]
**Version:** 1.0
