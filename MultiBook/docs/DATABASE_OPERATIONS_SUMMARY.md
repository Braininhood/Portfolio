# Database Operations Summary - MultiBook

Quick reference guide for all database operations in the MultiBook application.

## Overview

- **Total Database Models:** 25 (20 implemented, 5 placeholders)
- **Total ViewSets/APIViews:** 28
- **Signal Handlers:** 1 (Order confirmation)
- **Database Write Operations:** ~80+ different save/update/delete operations

---

## Models by App

| App | Models | Description |
|-----|--------|-------------|
| `accounts` | 4 | User, Profile, Manager, Invitation |
| `customers` | 2 | Customer, Address |
| `staff` | 4 | Staff, StaffSchedule, StaffService, StaffArea |
| `services` | 2 | Category, Service |
| `appointments` | 2 | Appointment, CustomerAppointment |
| `orders` | 3 | Order, OrderItem, ChangeRequest |
| `subscriptions` | 3 | Subscription, SubscriptionAppointment, SubscriptionAppointmentChangeRequest |
| `coupons` | 2 | Coupon, CouponUsage |
| `payments` | 0 | (Placeholder - to be implemented) |
| `notifications` | 0 | (Placeholder - to be implemented) |
| `calendar_sync` | 0 | (Placeholder - to be implemented) |
| `core` | 1 | TimeStampedModel (base class) |

---

## Database Operations by Category

### CREATE Operations (22 models)

| Model | Endpoint | Permissions | Auto-Generated Fields |
|-------|----------|-------------|----------------------|
| **User** | `POST /api/auth/register/` | Public (customer) or Invitation (staff/manager/admin) | - |
| **Profile** | Auto-created with User | - | `timezone` |
| **Manager** | Created with User (role=manager) | Admin | - |
| **Invitation** | `POST /api/admin/invitations/` | Admin | `token`, `expires_at` |
| **Customer** | `POST /api/admin/customers/` or Auto with User | Admin/Manager or Auto | - |
| **Address** | `POST /api/admin/addresses/` | Admin/Manager/Customer | - |
| **Staff** | `POST /api/admin/staff/` | Admin/Manager | - |
| **StaffSchedule** | `POST /api/admin/staff-schedules/` | Admin/Manager | - |
| **StaffService** | `POST /api/admin/staff-services/` | Admin/Manager | - |
| **StaffArea** | `POST /api/admin/staff-areas/` | Admin/Manager | - |
| **Category** | `POST /api/admin/categories/` | Admin | `slug` |
| **Service** | `POST /api/admin/services/` | Admin/Staff | `slug` |
| **Appointment** | `POST /api/appointments/` or Auto (order confirmation) | Public/Customer or Auto | - |
| **CustomerAppointment** | Auto with Appointment | Auto | `cancellation_deadline` |
| **Order** | `POST /api/orders/` | Public | `order_number`, `tracking_token`, `cancellation_deadline` |
| **OrderItem** | Created with Order | Public | `total_price` |
| **ChangeRequest** | `POST /api/orders/{id}/change-requests/` | Customer/Guest | - |
| **Subscription** | `POST /api/subscriptions/` | Public/Customer | `subscription_number`, `tracking_token`, `end_date`, `total_appointments` |
| **SubscriptionAppointment** | Auto (subscription generation) | Auto | `cancellation_deadline` |
| **SubscriptionAppointmentChangeRequest** | `POST /api/subscriptions/{id}/change-requests/` | Customer/Guest | - |
| **Coupon** | `POST /api/admin/coupons/` | Admin | - |
| **CouponUsage** | Auto (coupon application) | Auto | - |

### UPDATE Operations (18 models)

| Model | Common Updates | Triggered By |
|-------|----------------|--------------|
| **User** | `role`, `is_verified`, `email` | Admin, Verification |
| **Profile** | `phone`, `avatar`, `timezone`, `calendar_sync_enabled`, `calendar_access_token` | User, Calendar Connect |
| **Manager** | `permissions`, `managed_staff`, `managed_customers` | Admin |
| **Invitation** | `used_at`, `is_active` | Registration |
| **Customer** | `name`, `email`, `phone`, `address`, `notes`, `tags` | Admin/Manager |
| **Staff** | `name`, `email`, `phone`, `bio`, `photo`, `is_active` | Admin/Manager |
| **StaffSchedule** | `start_time`, `end_time`, `breaks` | Admin/Manager |
| **StaffService** | `price_override`, `duration_override` | Admin/Manager |
| **Service** | `price`, `duration`, `extras`, `approval_status`, `is_active` | Admin |
| **Appointment** | `status`, `start_time`, `end_time`, `internal_notes`, `completion_photos`, `calendar_event_id` | Admin/Manager/Staff, Calendar Sync |
| **CustomerAppointment** | `payment_status`, `can_cancel`, `can_reschedule` | Payment, Time-based |
| **Order** | `status`, `scheduled_date`, `scheduled_time`, `customer`, `can_cancel`, `can_reschedule` | Admin/Manager, Account Link |
| **OrderItem** | `staff`, `appointment` | Admin/Manager, Order Confirmation |
| **ChangeRequest** | `status`, `reviewed_by`, `reviewed_at`, `review_notes` | Admin/Manager |
| **Subscription** | `status`, `next_appointment_date`, `completed_appointments` | Admin/Manager, Appointment Completion |
| **SubscriptionAppointment** | `status`, `can_cancel`, `can_reschedule` | Staff, Time-based |
| **Coupon** | `used_count`, `status` | Coupon Usage, Expiry |
| **CouponUsage** | (Tracking only - rarely updated) | - |

### DELETE Operations (5 models)

| Model | Delete Type | Endpoint | Can Delete? |
|-------|-------------|----------|-------------|
| **Invitation** | Hard Delete | `DELETE /api/admin/invitations/{id}/` | ✅ Unused/expired only |
| **Address** | Hard Delete | `DELETE /api/admin/addresses/{id}/` | ✅ Not if is_default |
| **StaffSchedule** | Hard Delete | `DELETE /api/admin/staff-schedules/{id}/` | ✅ Yes |
| **StaffArea** | Hard Delete | `DELETE /api/admin/staff-areas/{id}/` | ✅ Yes |
| **StaffService** | Hard Delete | `DELETE /api/admin/staff-services/{id}/` | ✅ Yes |

### SOFT DELETE (7 models)

| Model | Soft Delete Method | Field |
|-------|-------------------|-------|
| **User** | Set inactive | `is_active = False` |
| **Staff** | Set inactive | `is_active = False` |
| **Service** | Set inactive | `is_active = False` |
| **Appointment** | Cancel | `status = 'cancelled'` |
| **Order** | Cancel | `status = 'cancelled'` |
| **Subscription** | Cancel | `status = 'cancelled'` |
| **Coupon** | Deactivate | `status = 'inactive'` |

---

## Auto-Save Behaviors

### Model `save()` Overrides

| Model | Auto-Generated/Calculated Fields |
|-------|----------------------------------|
| **User** | Normalizes `email` to lowercase |
| **Customer** | Sets `user.role = 'customer'` if user linked |
| **Staff** | Sets `user.role = 'staff'` if user linked |
| **Category** | Generates `slug` from `name` |
| **Service** | Generates `slug` from `name` |
| **Order** | Generates `order_number`, `tracking_token`, calculates `cancellation_deadline` |
| **OrderItem** | Calculates `total_price = quantity × unit_price` |
| **Subscription** | Generates `subscription_number`, `tracking_token`, calculates `end_date` |
| **SubscriptionAppointment** | Calculates `cancellation_deadline` (24h before start) |
| **Invitation** | Generates `token`, sets `expires_at = now() + 7 days` |
| **Coupon** | Validates `discount_value` ≤ 100% (percentage), auto-updates `status` if expired |

### Django Signals

| Signal | Model | Trigger | Actions |
|--------|-------|---------|---------|
| **pre_save** | Order | `status` → 'confirmed' | 1. Create Appointments for OrderItems<br>2. Create CustomerAppointments<br>3. Sync to calendars (customer, staff, manager)<br>4. Send confirmation email |

---

## Complex Database Operations

### 1. Order Confirmation (Triggered by Signal)

**Database writes per 2-item order:**
- 1× UPDATE: `Order.status`
- 2× CREATE: `Appointment`
- 2× UPDATE: `OrderItem.appointment`
- 2× CREATE: `CustomerAppointment`
- 4× UPDATE: `Appointment.calendar_event_id` (customer + staff sync)
- 4× UPDATE: `Appointment.calendar_synced_to`

**Total:** 13 database operations

---

### 2. Subscription Creation & Generation

**Initial creation:**
- 1× CREATE: `Subscription`

**Appointment generation (e.g., 12 visits):**
- 12× CREATE: `Appointment`
- 12× CREATE: `SubscriptionAppointment`
- 12× UPDATE: `Appointment.calendar_event_id` (if synced)

**Total:** 37 database operations (for 12-visit subscription)

---

### 3. Guest Order → Account Link

**When guest registers:**
- 1× CREATE: `User`
- 1× CREATE: `Profile`
- 1× CREATE: `Customer`
- 1× UPDATE: `Order.customer` (link existing order)
- N× CREATE: `CustomerAppointment` (for all order appointments)

**Total:** 3 CREATEs + 1 UPDATE + N CREATEs

---

### 4. Coupon Application

**Per coupon use:**
- 1× READ: `Coupon` (validate)
- 1× READ: `CouponUsage` (check per-customer limit)
- 1× CREATE: `CouponUsage`
- 1× UPDATE: `Coupon.used_count++`
- 1× UPDATE: `Order.total_price` (apply discount)

**Total:** 5 database operations (2 reads, 1 create, 2 updates)

---

### 5. Appointment Reschedule (Subscription)

**Per reschedule request:**
- 1× CREATE: `SubscriptionAppointmentChangeRequest`
- 1× UPDATE: `SubscriptionAppointmentChangeRequest.status` (when reviewed)
- 1× UPDATE: `Appointment.start_time` (when approved)
- 1× UPDATE: `Appointment.end_time`
- N× UPDATE: `Appointment.calendar_event_id` (update calendar events)

**Total:** 1 CREATE + 3 UPDATEs + N UPDATEs

---

## Permission Matrix

| Role | Can Create | Can Update | Can Delete |
|------|-----------|-----------|-----------|
| **Customer** | Orders, Subscriptions, Appointments (own) | Profile (own), Addresses (own) | Addresses (own) |
| **Staff** | Services (pending approval) | Appointments (own), Profile (own) | - |
| **Manager** | Staff, Customers, Schedules, Areas | Staff, Customers, Orders, Appointments (managed scope) | Schedules, Areas |
| **Admin** | All | All | All |
| **Guest** | Orders, Subscriptions | Orders (via tracking_token) | - |

---

## API Endpoints Summary

### Public Endpoints (No Auth)
- `POST /api/auth/register/` - User registration
- `POST /api/orders/` - Create guest order
- `POST /api/subscriptions/` - Create guest subscription
- `POST /api/appointments/` - Book appointment
- `GET /api/services/` - List services
- `GET /api/staff/` - List staff (public profiles)

### Customer Endpoints (Auth Required)
- `GET /api/cus/dashboard/` - Customer dashboard
- `GET /api/cus/appointments/` - My appointments
- `GET /api/cus/orders/` - My orders
- `GET /api/cus/subscriptions/` - My subscriptions
- `PATCH /api/profile/` - Update profile

### Admin/Manager Endpoints
- `GET/POST/PATCH/DELETE /api/admin/users/`
- `GET/POST/PATCH/DELETE /api/admin/customers/`
- `GET/POST/PATCH/DELETE /api/admin/staff/`
- `GET/POST/PATCH/DELETE /api/admin/services/`
- `GET/POST/PATCH/DELETE /api/admin/orders/`
- `GET/POST/PATCH/DELETE /api/admin/appointments/`
- `GET/POST/PATCH/DELETE /api/admin/coupons/`

### Staff Self-Service Endpoints
- `GET /api/staff/my-appointments/` - My assigned appointments
- `POST /api/staff/services/` - Create service (pending approval)
- `PATCH /api/staff/my-schedule/` - Update schedule
- `POST /api/staff/my-areas/` - Add service area

---

## Database Relationships

### Foreign Keys (ON_DELETE behavior)

| From → To | ON_DELETE | Effect |
|-----------|-----------|--------|
| Profile → User | CASCADE | Delete profile if user deleted |
| Manager → User | CASCADE | Delete manager profile if user deleted |
| Customer → User | SET_NULL | Keep customer record if user deleted |
| Staff → User | SET_NULL | Keep staff record if user deleted |
| Order → Customer | SET_NULL | Keep order if customer deleted |
| OrderItem → Order | CASCADE | Delete items if order deleted |
| Appointment → Staff | CASCADE | Delete appointment if staff deleted |
| Appointment → Service | CASCADE | Delete appointment if service deleted |
| CustomerAppointment → Appointment | CASCADE | Delete booking if appointment deleted |
| Subscription → Service | CASCADE | Delete subscription if service deleted |
| CouponUsage → Coupon | CASCADE | Delete usage records if coupon deleted |

### Many-to-Many Relationships

| Model | Related To | Through | Purpose |
|-------|------------|---------|---------|
| Staff | Service | StaffService | Staff-service assignments with custom pricing |
| Coupon | Service | (direct) | Service restrictions (applicable_services, excluded_services) |
| Manager | Staff | (direct) | Manager can manage specific staff members |
| Manager | Customer | (direct) | Manager can manage specific customers |

---

## Validation Rules

### Business Logic Validations

| Model | Validation | Enforced By |
|-------|-----------|-------------|
| **Coupon** | `discount_value` ≤ 100% (percentage) | Model `save()` |
| **Order** | Guest order requires `guest_email` | Serializer validation |
| **Appointment** | Cannot book in past | View validation |
| **Appointment** | Cannot cancel within 24h | View validation (`can_cancel` check) |
| **CustomerAppointment** | `cancellation_deadline` calculated as start_time - 24h | Model `save()` |
| **StaffSchedule** | Unique per staff + day_of_week | Database constraint |
| **StaffService** | Unique per staff + service | Database constraint |
| **Invitation** | Email must match when registering | View validation |
| **Invitation** | Cannot use expired invitation | View validation |
| **CouponUsage** | Check per-customer limit before use | Coupon `is_valid()` method |

---

## Indexing Strategy

### Database Indexes

| Model | Indexed Fields | Purpose |
|-------|---------------|---------|
| **User** | `email` (unique) | Fast login lookup |
| **Order** | `order_number` (unique), `tracking_token` (unique), `postcode` | Fast order lookup, guest access |
| **Subscription** | `subscription_number` (unique), `tracking_token` (unique) | Fast subscription lookup |
| **Appointment** | `staff + start_time`, `status + start_time` | Calendar queries, availability checks |
| **Coupon** | `code` (unique), `status + valid_from + valid_until` | Fast coupon lookup, validity checks |
| **Customer** | `email`, `postcode`, `user` | Fast customer search |
| **Staff** | `is_active + email` | Active staff queries |
| **StaffArea** | `postcode + is_active`, `staff + is_active` | Postcode coverage checks |

---

## Recommended Improvements

### 1. Add Payment Models
- `Payment` - Track payments (Stripe integration)
- `Invoice` - Generate invoices
- `Refund` - Track refunds

### 2. Add Notification Models
- `EmailLog` - Track sent emails
- `SMSLog` - Track sent SMS
- `NotificationPreference` - Per-user notification settings

### 3. Add Audit Trail
- `AuditLog` - Track all CUD operations
  - Fields: user, action, model, old_value, new_value, timestamp

### 4. Add Review System
- `Review` - Customer reviews for services/staff
- `Rating` - Numeric ratings

### 5. Optimize Queries
- Add `select_related()` and `prefetch_related()` to views
- Implement database-level caching (Redis)
- Add read replicas for reporting queries

### 6. Add Data Validation
- Implement `clean()` methods on all models
- Add database CHECK constraints
- Add custom validators for phone numbers, postcodes

---

**Last Updated:** 2026-02-15  
**Version:** 1.0  
**See Also:**
- [DATABASE_OPERATIONS_ANALYSIS.md](./DATABASE_OPERATIONS_ANALYSIS.md) - Detailed analysis
- [DATABASE_FLOW_DIAGRAMS.md](./DATABASE_FLOW_DIAGRAMS.md) - Visual flow diagrams
