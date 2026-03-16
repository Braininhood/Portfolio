# MultiBook Booking System - Technical Architecture

## Overview

This document provides a detailed technical architecture for the MultiBook booking system, covering system design, technology choices, data flow, and scalability considerations.

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web App    │  │  Mobile Web   │  │ Manager Panel│  │  Admin Panel  │         │
│  │  (Next.js)   │  │   (PWA)       │  │  (Next.js)  │  │  (Next.js)    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                │
│                            │                                     │
│                    ┌───────▼────────┐                           │
│                    │   API Gateway   │                           │
│                    │  (Nginx/CloudFlare)                         │
│                    └───────┬────────┘                           │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────────┐
│                    ┌───────▼────────┐                           │
│                    │  Load Balancer  │                           │
│                    │   (Optional)    │                           │
│                    └───────┬────────┘                           │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐          │
│  │   Django     │  │   Django       │  │   Django     │          │
│  │   API Server │  │   API Server   │  │   API Server │          │
│  │  (Instance 1)│  │  (Instance 2)  │  │  (Instance N)│          │
│  └──────┬───────┘  └───────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                 │
│                            │                                     │
│                    ┌───────▼────────┐                           │
│                    │   Application   │                           │
│                    │     Layer       │                           │
│                    └───────┬────────┘                           │
│                            │                                     │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐          │
│  │  SQLite     │  │     Redis     │  │   Celery    │          │
│  │  (Dev)      │  │   (Cache/Queue)│  │  (Workers)  │          │
│  │ PostgreSQL  │  │   (Optional)   │  │ (Optional)  │          │
│  │  (Prod)     │  │                │  │            │          │
│  └─────────────┘  └────────────────┘  └─────────────┘          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │         External Services Integration                  │       │
│  │  Stripe | PayPal | Twilio | SendGrid | Google Maps | Google Places API   │       │
│  └──────────────────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Architecture

#### Frontend (Next.js)
```
Next.js Application
├── App Router (App Directory)
│   ├── (auth)/          # Authentication routes
│   ├── (customer)/      # Customer portal
│   ├── (staff)/         # Staff portal
│   ├── (manager)/       # Manager dashboard (permission-based)
│   ├── (admin)/         # Admin panel
│   └── booking/         # Public booking flow
│
├── Components
│   ├── ui/              # shadcn/ui components
│   ├── booking/         # Booking-specific
│   ├── calendar/       # Calendar components
│   └── forms/          # Form components
│
├── Lib
│   ├── api/            # API client
│   ├── hooks/          # Custom React hooks
│   └── utils/          # Utility functions
│
└── Store
    └── Zustand stores  # State management
```

#### Backend (Django)
```
Django Application
├── config/             # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
│
├── apps/
│   ├── core/          # Core utilities
│   ├── accounts/      # Authentication
│   ├── services/      # Services management
│   ├── staff/         # Staff management
│   ├── customers/     # Customer management
│   ├── appointments/  # Booking system
│   ├── payments/      # Payment processing
│   ├── notifications/ # Email/SMS
│   ├── calendar_sync/ # Calendar sync
│   └── api/            # REST API
│
└── requirements.txt
```

---

## 2. Technology Stack Details

### 2.1 Frontend Stack

#### Next.js 14+ (App Router)
```typescript
// Why Next.js App Router?
- Server Components for better performance
- Built-in routing and layouts
- API routes for serverless functions
- Image optimization
- Automatic code splitting
- TypeScript support
- SEO-friendly (SSR/SSG)
```

**Key Packages:**
```json
{
  "next": "^14.0.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "@radix-ui/react-*": "Latest",
  "zustand": "^4.4.0",
  "react-hook-form": "^7.48.0",
  "zod": "^3.22.0",
  "axios": "^1.6.0",
  "date-fns": "^2.30.0",
  "fullcalendar": "^6.1.0",
  "@tanstack/react-query": "^5.0.0"
}
```

#### Styling: Tailwind CSS + shadcn/ui
```typescript
// Why Tailwind + shadcn/ui?
- Utility-first CSS (fast development)
- Consistent design system
- Accessible components
- Easy customization
- Small bundle size
```

### 2.2 Backend Stack

#### Django 5.0+
```python
# Why Django?
- Rapid development
- Built-in admin panel
- Excellent ORM
- Security features
- Large ecosystem
- Great documentation
```

**Key Packages:**
```python
# requirements.txt
Django==5.0.0
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
django-cors-headers==4.3.0
django-environ==0.11.0
psycopg2-binary==2.9.9
redis==5.0.0
celery==5.3.0
django-celery-beat==2.5.0
stripe==7.0.0
paypalrestsdk==1.13.0
twilio==8.10.0
sendgrid==6.11.0
google-api-python-client==2.100.0
msal==1.25.0
drf-spectacular==0.26.0
```

#### Database: SQLite (Development) / PostgreSQL (Production)
```sql
-- Development: SQLite
- No setup required
- File-based database (db.sqlite3)
- Perfect for local development
- Easy to reset and test

-- Production: PostgreSQL 15+
- ACID compliance
- Advanced features (JSON, arrays)
- Excellent performance
- Full-text search
- Extensions (PostGIS for maps)
- Mature and stable
```

#### Cache & Queue: Redis 7+
```python
# Why Redis?
- Fast in-memory storage
- Pub/sub for real-time
- Session storage
- Celery broker
- Rate limiting
- Caching
```

#### Task Queue: Celery
```python
# Why Celery?
- Async task processing
- Scheduled tasks (reminders)
- Background jobs
- Email/SMS sending
- Calendar sync
- Report generation
```

---

## 3. Data Flow

### 3.1 Booking Flow Data Flow

```
1. Customer selects service
   Frontend → API: GET /api/svc/{id}/ (Security: shortened prefix)
   Backend → Database: Query Service
   Backend → Frontend: Service details

2. Customer selects date/time
   Frontend → API: GET /api/slots/?service_id=X&date=Y (Security: shortened prefix)
   Backend → Database: Query appointments, staff schedules
   Backend → Logic: Calculate available slots
   Backend → Cache: Store available slots (Redis)
   Backend → Frontend: Available time slots

3. Customer enters details
   Frontend → API: POST /api/addr/autocomplete/ (Security: shortened prefix, Google Places)
   External API → Frontend: Address suggestions
   Frontend → Backend: Customer details
   Backend → Database: Create/Update Customer

4. Customer makes payment
   Frontend → API: POST /api/pay/create-intent/ (Security: shortened prefix)
   Backend → Stripe: Create PaymentIntent
   Stripe → Backend: PaymentIntent ID
   Backend → Frontend: Client secret
   Frontend → Stripe: Confirm payment
   Stripe → Backend: Webhook (payment succeeded)
   Backend → Database: Create Appointment, Payment
   Backend → Celery: Send confirmation emails
   Backend → Calendar: Create calendar event
   Backend → Frontend: Booking confirmation
```

### 3.2 Real-Time Updates Flow

```
1. WebSocket Connection
   Frontend → Backend: WebSocket connection
   Backend → Redis: Subscribe to channels

2. Appointment Update
   Admin → API: PUT /api/appointments/{id}/
   Backend → Database: Update appointment
   Backend → Redis: Publish update event
   Redis → All connected clients: Broadcast update
   Frontend: Update UI in real-time
```

### 3.3 Notification Flow

```
1. Appointment Created
   Backend → Celery: Queue email task
   Celery Worker → SendGrid: Send email
   SendGrid → Customer: Email delivered
   Backend → Database: Log notification

2. Reminder Scheduled
   Celery Beat → Celery: Schedule reminder task
   (24 hours before appointment)
   Celery Worker → SendGrid/Twilio: Send reminder
   Backend → Database: Log reminder sent
```

---

## 4. Database Design

### 4.1 Core Tables

```sql
-- Users and Authentication
users (extends Django User)
├── id (PK)
├── email (unique)
├── username
├── password_hash
├── role (enum: admin, manager, staff, customer)
├── is_active
├── is_staff
├── is_superuser
└── date_joined

managers
├── id (PK)
├── user_id (FK → users, OneToOne)
├── permissions (JSONB) - permission configuration
├── can_manage_all (boolean)
├── managed_locations (M2M → locations, nullable)
├── managed_staff (M2M → staff, nullable)
├── managed_customers (M2M → customers, nullable)
└── created_at

profiles
├── id (PK)
├── user_id (FK → users)
├── phone
├── avatar_url
├── timezone
├── preferences (JSONB)
├── calendar_sync_enabled (boolean)
├── calendar_provider (enum: google, outlook, apple, none)
├── calendar_access_token (encrypted, nullable)
├── calendar_refresh_token (encrypted, nullable)
├── calendar_calendar_id (string, nullable)
└── calendar_sync_settings (JSONB) - sync preferences

-- Services
categories
├── id (PK)
├── name
├── slug (unique)
├── description
├── image_url
├── position
└── is_active

services
├── id (PK)
├── category_id (FK → categories)
├── name
├── slug (unique)
├── description
├── duration_minutes
├── price
├── currency
├── image_url
├── color (hex)
├── capacity
├── padding_time
├── is_active
└── position

-- Staff
staff
├── id (PK)
├── user_id (FK → users, nullable)
├── name
├── email
├── phone
├── photo_url
├── bio
├── is_active
└── position
# Note: Calendar sync now handled in profiles table for all users

staff_schedules
├── id (PK)
├── staff_id (FK → staff)
├── day_of_week (0-6)
├── start_time
├── end_time
└── breaks (JSONB)

staff_services
├── id (PK)
├── staff_id (FK → staff)
├── service_id (FK → services)
├── price_override
└── duration_override

staff_areas
├── id (PK)
├── staff_id (FK → staff)
├── postcode (string) - center postcode
├── radius_km (decimal) - service radius in kilometers
├── is_active (boolean)
├── created_at
└── updated_at

-- Customers
customers
├── id (PK)
├── user_id (FK → users, nullable)
├── name
├── email
├── phone
├── address_line1
├── address_line2
├── city
├── county
├── postcode
├── country
├── address_validated (boolean)
├── notes (text)
├── tags (JSONB)
└── created_at

-- Appointments
appointments
├── id (PK)
├── staff_id (FK → staff)
├── service_id (FK → services)
├── start_time (timestamp)
├── end_time (timestamp)
├── status (enum)
├── appointment_type (enum: single, subscription, order_item)
├── subscription_id (FK → subscriptions, nullable)
├── order_id (FK → orders, nullable)
├── calendar_event_id (JSONB) - stores event IDs for each provider
├── calendar_synced_to (JSONB) - tracks which calendars event is synced to
├── location_id (FK → locations, nullable)
├── internal_notes (text)
└── created_at

customer_appointments
├── id (PK)
├── customer_id (FK → customers)
├── appointment_id (FK → appointments)
├── number_of_persons
├── extras (JSONB)
├── custom_fields (JSONB)
├── total_price
├── deposit_paid
├── payment_status (enum)
├── cancellation_token (uuid)
├── can_cancel (boolean)
├── can_reschedule (boolean)
├── cancellation_deadline (timestamp)
└── created_at

-- Subscriptions
subscriptions
├── id (PK)
├── customer_id (FK → customers)
├── service_id (FK → services)
├── staff_id (FK → staff, nullable)
├── frequency (enum: weekly, biweekly, monthly)
├── duration_months (integer)
├── start_date (date)
├── end_date (date)
├── next_appointment_date (date)
├── status (enum)
├── total_appointments (integer)
├── completed_appointments (integer)
├── price_per_appointment (decimal)
├── total_price (decimal)
├── payment_status (enum)
├── cancellation_policy_hours (integer, default: 24)
├── created_at
└── updated_at

subscription_appointments
├── id (PK)
├── subscription_id (FK → subscriptions)
├── appointment_id (FK → appointments)
├── sequence_number (integer)
├── scheduled_date (date)
├── status (enum)
├── can_cancel (boolean)
└── cancellation_deadline (timestamp)

-- Orders
orders
├── id (PK)
├── customer_id (FK → customers)
├── order_number (string, unique)
├── status (enum)
├── total_price (decimal)
├── deposit_paid (decimal)
├── payment_status (enum)
├── scheduled_date (date)
├── scheduled_time (time, nullable)
├── cancellation_policy_hours (integer, default: 24)
├── can_cancel (boolean)
├── can_reschedule (boolean)
├── cancellation_deadline (timestamp)
├── created_at
└── updated_at

order_items
├── id (PK)
├── order_id (FK → orders)
├── service_id (FK → services)
├── staff_id (FK → staff, nullable)
├── appointment_id (FK → appointments, nullable)
├── quantity (integer)
├── price (decimal)
├── status (enum)
└── notes (text, nullable)

-- Payments
payments
├── id (PK)
├── customer_appointment_id (FK → customer_appointments)
├── amount
├── currency
├── payment_method (enum)
├── status (enum)
├── transaction_id
├── gateway_response (JSONB)
└── created_at

invoices
├── id (PK)
├── customer_id (FK → customers)
├── invoice_number (unique)
├── total_amount
├── tax_amount
├── status (enum)
├── due_date
├── paid_at
└── created_at
```

### 4.2 Indexes

```sql
-- Performance indexes
CREATE INDEX idx_appointments_staff_date ON appointments(staff_id, start_time);
CREATE INDEX idx_appointments_service_date ON appointments(service_id, start_time);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_customer_appointments_customer ON customer_appointments(customer_id);
CREATE INDEX idx_customer_appointments_appointment ON customer_appointments(appointment_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_staff_schedules_staff_day ON staff_schedules(staff_id, day_of_week);
CREATE INDEX idx_staff_areas_staff ON staff_areas(staff_id);
CREATE INDEX idx_staff_areas_postcode ON staff_areas(postcode);
CREATE INDEX idx_customers_postcode ON customers(postcode);
```

### 4.3 Database Optimization

**Query Optimization:**
- Use `select_related()` for foreign keys
- Use `prefetch_related()` for many-to-many
- Use `only()` and `defer()` for partial loads
- Use database indexes strategically
- Use `annotate()` and `aggregate()` for calculations

**Caching Strategy:**
- Cache service listings (1 hour)
- Cache services by postcode (30 minutes)
- Cache staff by postcode (30 minutes)
- Cache available slots (5 minutes)
- Cache staff schedules (1 hour)
- Cache customer data (30 minutes)
- Cache postcode-to-area mappings (24 hours)

---

## 5. API Design

### 5.1 REST API Structure

```
/api/v1/
# Public Endpoints (Security: Shortened prefixes to prevent enumeration)
├── aut/                    # Authentication (Security: /api/aut/)
│   ├── POST   /register/
│   ├── POST   /login/
│   ├── POST   /logout/
│   ├── POST   /refresh/
│   └── POST   /password-reset/
│
├── svc/                    # Services (Security: /api/svc/)
│   ├── GET    /                           # List all services
│   ├── GET    /by-postcode/               # Get services by postcode area
│   ├── GET    /{id}/
│   └── GET    /{id}/staff/                # Get staff for service in area
│
├── stf/                    # Staff (public listing) (Security: /api/stf/)
│   ├── GET    /                           # List all staff
│   ├── GET    /by-postcode/               # Get staff by postcode area
│   └── GET    /{id}/
│
├── bkg/                    # Bookings (Security: /api/bkg/)
│   ├── GET    /slots/                     # Get available slots (filtered by postcode)
│   ├── POST   /
│   ├── GET    /{id}/
│   ├── POST   /{id}/cancel/
│   └── POST   /{id}/reschedule/
│
├── addr/                   # Address (Security: /api/addr/)
│   ├── POST   /autocomplete/              # Google Places autocomplete
│   └── POST   /validate/                  # Address validation
│
├── slots/                  # Available Slots (Security: /api/slots/)
│   └── GET    /                           # Get available time slots
│
# Protected Role-Based Endpoints (Security: Shortened prefixes to prevent enumeration)
├── cus/                    # Customer endpoints (Security: /api/cus/)
│   ├── GET    /profile/
│   ├── PUT    /profile/
│   ├── GET    /appointments/
│   ├── GET    /subscriptions/
│   ├── GET    /orders/
│   └── GET    /invoices/
│
├── st/                     # Staff endpoints (Security: /api/st/)
│   ├── GET    /schedule/
│   ├── GET    /jobs/
│   └── PUT    /availability/
│
├── man/                    # Manager endpoints (Security: /api/man/)
│   ├── GET    /appointments/
│   ├── GET    /staff/
│   ├── GET    /customers/
│   └── GET    /reports/
│
├── ad/                     # Admin endpoints (Security: /api/ad/)
│   ├── appointments/
│   ├── staff/
│   ├── customers/
│   ├── managers/
│   ├── services/
│   └── reports/
│
├── pay/                    # Payments (Security: /api/pay/)
│   ├── POST   /create-intent/
│   ├── POST   /confirm/
│   └── POST   /webhook/
```

### 5.2 API Response Format

```json
// Success Response
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}

// Error Response
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": ["Error message"]
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

### 5.3 Authentication

**JWT Token Flow:**
```
1. User logs in
   POST /api/aut/login/ (Security: shortened prefix)
   → Returns: access_token, refresh_token

2. Authenticated requests
   Header: Authorization: Bearer {access_token}

3. Token refresh
   POST /api/aut/refresh/ (Security: shortened prefix)
   → Returns: new access_token

4. Token expiration
   Access token: 15 minutes
   Refresh token: 7 days
```

---

## 6. Security Architecture

### 6.1 Security Layers

```
1. Network Layer
   - HTTPS/TLS encryption
   - DDoS protection (CloudFlare)
   - Rate limiting

2. Application Layer
   - JWT authentication
   - Role-based access control
   - Input validation
   - SQL injection prevention
   - XSS prevention
   - CSRF protection

3. Data Layer
   - Database encryption at rest
   - PII data encryption
   - Secure password hashing (bcrypt)
   - Secure session management

4. Infrastructure Layer
   - Secure environment variables
   - Secret management
   - Regular security updates
   - Security monitoring
```

### 6.2 Security Best Practices

**Authentication:**
- JWT tokens with short expiration
- Refresh token rotation
- Secure token storage (httpOnly cookies)
- Two-factor authentication (optional)

**Authorization:**
- Role-based access control (RBAC)
- Permission-based endpoints
- Row-level security
- API key management

**Data Protection:**
- Encrypt sensitive data
- GDPR compliance
- Data retention policies
- Regular backups
- Secure data deletion

### 6.3 Endpoint Security (Shortened Prefixes)

**Security Rationale:** ALL endpoints (both public and protected) use shortened prefixes to prevent enumeration attacks and make endpoints less predictable.

**Public Endpoint Prefixes:**
| Original Endpoint | Security Prefix | Purpose |
|------------------|-----------------|---------|
| `/api/services/` | `/api/svc/` | Service listings and details |
| `/api/staff/` | `/api/stf/` | Public staff listings (postcode-based) |
| `/api/bookings/` | `/api/bkg/` | Booking creation and management |
| `/api/address/` | `/api/addr/` | Google Places autocomplete |
| `/api/auth/` | `/api/aut/` | Authentication endpoints |
| `/api/available-slots/` | `/api/slots/` | Available time slots |
| `/api/payments/` | `/api/pay/` | Payment processing |

**Protected Endpoint Prefixes (Role-Based):**
| Original Endpoint | Security Prefix | Access Level |
|------------------|-----------------|--------------|
| `/api/customer/` | `/api/cus/` | Customer role required |
| `/api/staff/` | `/api/st/` | Staff role required (different from public `/api/stf/`) |
| `/api/manager/` | `/api/man/` | Manager role required |
| `/api/admin/` | `/api/ad/` | Admin role required |

**Security Benefits:**
1. **Endpoint Enumeration Prevention:** Attackers cannot easily guess endpoint names
2. **Reduced Attack Surface:** Shortened prefixes hide the structure of the API
3. **Security Through Obscurity:** Adds an additional layer (should be combined with proper authentication)
4. **Consistent Pattern:** All endpoints follow the same security pattern

**Implementation Notes:**
- All endpoints require proper authentication/authorization checks
- Shortened prefixes are documented only in internal documentation
- Rate limiting applies to all endpoints regardless of prefix
- API versioning still supported: `/api/v1/svc/`, `/api/v1/cus/`, etc.

---

## 7. Scalability Considerations

### 7.1 Horizontal Scaling

**Frontend:**
- Static assets on CDN
- Serverless functions (Vercel)
- Edge caching

**Backend:**
- Multiple Django instances
- Load balancer
- Database connection pooling
- Read replicas (PostgreSQL)

**Database:**
- Primary/Replica setup
- Connection pooling (PgBouncer)
- Query optimization
- Partitioning (if needed)

### 7.2 Caching Strategy

```
Level 1: Browser Cache
- Static assets (1 year)
- API responses (short-term)

Level 2: CDN Cache
- Static files
- API responses (edge caching)

Level 3: Application Cache (Redis)
- Service listings (1 hour)
- Available slots (5 minutes)
- Staff schedules (1 hour)
- User sessions

Level 4: Database Cache
- Query result caching
- Materialized views
```

### 7.3 Performance Optimization

**Frontend:**
- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization
- Service workers (PWA)

**Backend:**
- Database query optimization
- Caching frequently accessed data
- Background task processing
- API response compression
- Connection pooling

---

## 8. Monitoring & Logging

### 8.1 Monitoring Stack

```
Application Monitoring
├── Sentry (Error tracking)
├── New Relic / Datadog (APM)
└── Custom dashboards

Infrastructure Monitoring
├── Server metrics (CPU, memory, disk)
├── Database performance
├── Redis performance
└── Celery worker status

Business Metrics
├── Booking conversion rate
├── Payment success rate
├── User engagement
└── Revenue metrics
```

### 8.2 Logging Strategy

```python
# Logging levels
- ERROR: Critical errors requiring attention
- WARNING: Potential issues
- INFO: Important events (bookings, payments)
- DEBUG: Development debugging

# Log destinations
- Application logs → File / CloudWatch
- Error logs → Sentry
- Access logs → Nginx logs
- Business events → Analytics platform
```

---

## 9. Deployment Architecture

### 9.1 Development Environment

```
Local Development (Confirmed)
├── Django dev server (localhost:8000)
├── Next.js dev server (localhost:3000)
├── SQLite database (db.sqlite3)
├── Redis (Optional - can use in-memory cache)
└── Celery (Optional - can run sync for dev)

Development Setup:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- Database: SQLite file in project root

Tools
├── Hot reload (both frontend and backend)
├── Debug tools
└── Django debug toolbar (optional)
```

### 9.2 Production Environment

```
Frontend (Vercel)
├── Next.js build
├── Edge functions
├── CDN distribution
└── Automatic deployments

Backend (Railway/Render/AWS)
├── Django application
├── Gunicorn/Uvicorn
├── Nginx reverse proxy
└── Auto-scaling

Database (Managed PostgreSQL)
├── Primary database
├── Automated backups
├── Point-in-time recovery
└── Monitoring

Cache & Queue (Redis Cloud)
├── Redis cache
├── Celery broker
└── Session storage

External Services
├── Stripe (payments)
├── Twilio (SMS)
├── SendGrid (email)
└── Google Maps (routing)
```

### 9.3 CI/CD Pipeline

```
1. Code Push
   └─> GitHub/GitLab

2. Automated Tests
   └─> Unit tests
   └─> Integration tests
   └─> E2E tests

3. Code Quality
   └─> Linting (ESLint, Flake8)
   └─> Type checking (TypeScript, mypy)
   └─> Security scan

4. Build
   └─> Frontend build (Next.js)
   └─> Backend build (Django)
   └─> Docker images

5. Deploy
   └─> Staging environment
   └─> Manual approval
   └─> Production deployment

6. Post-Deploy
   └─> Health checks
   └─> Smoke tests
   └─> Monitoring alerts
```

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

```
Database Backups
├── Daily full backups
├── Hourly incremental backups
├── 30-day retention
└─> Off-site storage

Application Backups
├── Code repository (Git)
├── Media files (S3)
├── Configuration files
└─> Environment variables (secure storage)
```

### 10.2 Recovery Procedures

```
Database Recovery
├── Point-in-time recovery
├── Restore from backup
└─> Data validation

Application Recovery
├── Rollback to previous version
├── Restore from Git
└─> Health checks

Disaster Recovery Plan
├── RTO: 4 hours (Recovery Time Objective)
├── RPO: 1 hour (Recovery Point Objective)
└─> Regular DR drills
```

---

## 11. Future Enhancements

### 11.1 Planned Features

**Phase 6+ (Post-MVP):**
- Native mobile apps (React Native)
- Advanced AI features (chatbot, recommendations)
- Multi-location support
- Accounting software integration
- CRM integration
- Marketing automation
- Video conferencing integration
- Advanced analytics (ML-based insights)

### 11.2 Technical Improvements

- GraphQL API (optional)
- WebSocket for real-time updates
- Microservices architecture (if needed)
- Kubernetes deployment
- Multi-region deployment
- Advanced caching strategies
- Machine learning integration

---

*This architecture document provides the technical foundation for building a scalable, secure, and maintainable booking system.*

**Last Updated:** [Current Date]
**Version:** 1.0
