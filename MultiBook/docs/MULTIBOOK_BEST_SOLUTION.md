# MultiBook - Best Professional Solution

## Executive Summary

This document outlines the **best-in-class booking and management system** for MultiBook (https://yourdomain.com/), combining the best features from HouseCallPro and Bookly plugin, designed to be intuitive and easy-to-use for all types of users.

**User Roles:**
- 👤 **Customer** - Book services, manage appointments, view history
- 👷 **Staff** - View schedule, manage jobs, check-in/check-out
- 👔 **Manager** - Flexible permissions (manage customers, staff, or both based on admin assignment; can be location-based)
- 👑 **Admin** - Complete system control and configuration

**Goal**: Create a world-class booking system that is:
- ✅ **Easy for customers** - Simple, intuitive booking process
- ✅ **Guest Checkout** - No login/registration required - Perfect for elderly customers
- ✅ **Powerful for staff** - Comprehensive job management tools
- ✅ **Flexible for managers** - Customizable permissions and access
- ✅ **Efficient for admins** - Complete control and analytics
- ✅ **Modern & Scalable** - Built with Next.js + Django
- ✅ **Professional** - Enterprise-grade features and reliability

---

## Table of Contents

1. [Competitive Analysis](#1-competitive-analysis)
2. [Solution Architecture](#2-solution-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Core Features & User Experience](#4-core-features--user-experience)
5. [Implementation Phases](#5-implementation-phases)
6. [User Journey Maps](#6-user-journey-maps)
7. [Technical Specifications](#7-technical-specifications)
8. [Success Metrics](#8-success-metrics)

---

## 1. Competitive Analysis

### 1.1 HouseCallPro - Key Features Analysis

**Strengths:**
- ✅ **Field Service Management** - Complete dispatch and scheduling system
- ✅ **Customer Portal** - Self-service booking and history
- ✅ **Mobile App** - Native apps for staff and customers
- ✅ **Route Optimization** - Smart routing for field staff
- ✅ **Invoicing & Payments** - Integrated payment processing
- ✅ **Customer Communication** - Automated SMS/Email notifications
- ✅ **Job Management** - Status tracking, photos, signatures
- ✅ **Reporting & Analytics** - Comprehensive business insights
- ✅ **Team Management** - Staff scheduling and performance tracking
- ✅ **Integration Ecosystem** - Connects with accounting, marketing tools

**Key Learnings:**
- Mobile-first approach is critical
- Real-time updates and notifications are essential
- Route optimization saves time and money
- Customer self-service reduces admin workload
- Integrated payments streamline operations

### 1.2 Bookly Plugin - Key Features Analysis

**Strengths:**
- ✅ **Multi-Step Booking** - Guided booking process
- ✅ **Calendar Integration** - Google, Outlook, Apple Calendar sync
- ✅ **Flexible Scheduling** - Complex scheduling rules
- ✅ **Payment Gateways** - Multiple payment options
- ✅ **Custom Fields** - Flexible form customization
- ✅ **Recurring Appointments** - Repeat booking support
- ✅ **Coupons & Discounts** - Promotional code system
- ✅ **Notifications** - Email and SMS automation
- ✅ **Staff Management** - Multi-staff support with schedules
- ✅ **Service Packages** - Compound services and add-ons

**Key Learnings:**
- Multi-step booking reduces abandonment
- Calendar sync prevents double-booking
- Flexible scheduling rules accommodate complex businesses
- Custom fields capture business-specific data
- Recurring appointments increase customer retention

### 1.3 MultiBook-Specific Requirements

Based on MultiBook's cleaning services business:

**Must-Have Features:**
- 🎯 **Easy Booking** - Simple, fast booking for cleaning services
- 🎯 **Guest Checkout** - No login/registration required - Perfect for elderly customers
- 🎯 **Post-Order Account Linking** - Optional account creation/linking after order completion
- 🎯 **Address Management** - Google Places API for address autocomplete
- 🎯 **Postcode-First Booking** - Start with postcode, show area-specific services
- 🎯 **Staff Area Assignment** - Staff assigned to postcodes/areas with radius
- 🎯 **Service Packages** - Different cleaning service types
- 🎯 **Staff Assignment** - Assign cleaners to jobs
- 🎯 **Route Optimization** - Efficient scheduling for field staff
- 🎯 **Customer Portal** - View bookings, history, invoices (optional - guest orders work without)
- 🎯 **Mobile-Friendly** - Works perfectly on phones
- 🎯 **Payment Integration** - Secure online payments
- 🎯 **Notifications** - SMS and email confirmations
- 🎯 **Reporting** - Business analytics and insights

---

## 2. Solution Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MultiBook Booking System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Customer   │  │    Staff     │  │   Manager    │  │    Admin     │      │
│  │   Portal     │  │   Portal     │  │   Dashboard   │  │   Dashboard  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                  │
│                    ┌───────▼────────┐                        │
│                    │   API Gateway  │                        │
│                    │  (REST/GraphQL)│                        │
│                    └───────┬────────┘                        │
│                            │                                  │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                  │              │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐       │
│  │   Booking   │  │   Management   │  │  Analytics  │       │
│  │   Service   │  │    Service     │  │   Service   │       │
│  └─────────────┘  └────────────────┘  └─────────────┘       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Core Business Logic Layer                │   │
│  │  (Appointments, Services, Staff, Customers, Payments) │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Data Layer (PostgreSQL)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         External Integrations                          │   │
│  │  (Stripe, PayPal, Twilio, Google Calendar, etc.)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Principles

1. **Separation of Concerns**
   - Frontend (React/Vue/Next.js) - User interface
   - Backend API (Python/Django) - Business logic
   - Database (PostgreSQL) - Data storage
   - Cache (Redis) - Performance optimization

2. **API-First Design**
   - RESTful API for web and mobile
   - GraphQL for flexible queries (optional)
   - WebSocket for real-time updates

3. **Microservices-Ready**
   - Modular architecture
   - Service-oriented design
   - Easy to scale individual components

4. **Security-First**
   - HTTPS everywhere
   - JWT authentication
   - Role-based access control
   - Data encryption

5. **Performance-Optimized**
   - Caching strategy
   - Database indexing
   - CDN for static assets
   - Lazy loading

---

## 3. Technology Stack

### 3.1 Frontend Options Comparison

### 3.2 Technology Stack (Confirmed)

**Frontend: Next.js 14+ (App Router)** ⭐
- Server-side rendering (SEO-friendly)
- Built-in routing and API routes
- Excellent performance
- TypeScript support
- Easy deployment

**Backend: Django 5.0+** ⭐
- Rapid development
- Built-in admin panel
- Excellent ORM
- Security features
- Large ecosystem

#### Frontend: **Next.js 14+ (App Router)**
```typescript
// Why Next.js?
- Server-side rendering for SEO
- Built-in API routes
- Image optimization
- Automatic code splitting
- TypeScript support
- Easy deployment
```

**Frontend Technologies:**
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand or React Query
- **Forms**: React Hook Form + Zod validation
- **Calendar**: FullCalendar or React Big Calendar
- **Maps**: Google Maps API (for route optimization)
- **Real-time**: Socket.io client

#### Backend: **Django 5.0+ with Django REST Framework**
```python
# Confirmed: Django for backend
- Rapid development
- Built-in admin panel
- Excellent ORM
- Security features
- Large ecosystem
- Great documentation
```

**Backend Technologies:**
- **Framework**: Django 5.0+ with Django REST Framework
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Task Queue**: Celery + Redis
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Authentication**: djangorestframework-simplejwt
- **Real-time**: Django Channels (WebSocket)

#### Infrastructure:
- **Hosting**: 
  - Frontend: Vercel (Next.js) or Netlify
  - Backend: Railway, Render, or AWS
  - Database: Managed PostgreSQL (Supabase, Neon, or AWS RDS)
- **CDN**: Cloudflare or Vercel Edge
- **Monitoring**: Sentry (error tracking)
- **Analytics**: Google Analytics 4 + Custom dashboard

#### Third-Party Integrations:
- **Payments**: Stripe, PayPal
- **SMS**: Twilio
- **Email**: SendGrid or Resend
- **Calendar**: Google Calendar API, Microsoft Graph API
- **Address**: Google Places API (address autocomplete)
- **Maps**: Google Maps API
- **Storage**: AWS S3 or Cloudflare R2

---

## 4. Core Features & User Experience

### 4.1 Customer Experience (Easy for Everyone)

#### 4.1.1 Booking Flow - Guest Checkout (No Login Required)

**IMPORTANT: Booking starts WITHOUT login/registration. Perfect for elderly customers who don't want to create accounts.**

**Step 1: Enter Postcode** (10 seconds)
- Postcode input field
- Real-time validation
- Show available services in area
- Display service coverage map (optional)
- Mobile-optimized input
- **No login required** - booking accessible to everyone

**Step 2: Service Selection** (30 seconds)
- Show only services available in postcode area
- Visual service cards with images
- Clear pricing and duration
- One-click selection
- **Subscription option** (e.g., "Subscribe: Weekly cleaning for 3 months")
- **Add to order** option (select multiple services)
- Service comparison view
- Shows available staff for selected service in area
- Mobile-optimized layout
- **No account needed** - continue as guest

**Step 3: Date & Time** (20 seconds)
- Visual calendar picker
- Available time slots highlighted (only for staff in area)
- Smart suggestions (next available)
- Time zone detection
- Quick selection buttons
- Shows staff availability in postcode area
- **Guest-friendly** - no registration required

**Step 4: Booking Type Selection** (20 seconds)
- **Single Appointment** - One-time booking
- **Subscription** - Recurring service (weekly/biweekly/monthly)
  - Select frequency
  - Select duration (1, 2, 3, 6, 12 months)
  - Preview subscription schedule
- **Order** - Multiple services in one booking
  - Add multiple services
  - Set preferred date/time for order
  - View order summary
- **Works for guests** - no account creation required

**Step 5: Guest Details & Payment** (60 seconds)
- Simple form (name, email, phone, address)
- Address autocomplete (Google Places API)
- Auto-fill address from postcode
- **Guest checkout** - no login/registration required
- Clear pricing breakdown
- Multiple payment options
- Secure payment processing
- Instant confirmation
- Calendar file download (.ics)
- **Perfect for elderly customers** - simple and straightforward

**Step 6: Post-Order Account Linking (Optional)** (After order completion)
- **If customer email matches existing account:**
  - Show option: "Login to link this order to your account?"
  - Login modal with email pre-filled
  - After login: Order automatically linked to account
  - Customer can manage order from dashboard
  
- **If customer email doesn't match any account:**
  - Show option: "Create an account to manage your orders? (Optional)"
  - Registration option (one-click with pre-filled details from order)
  - Benefits shown: "Track orders, view history, faster rebooking"
  - **"Skip" button** - customer can continue without account
  
- **If customer doesn't want to register:**
  - Order works perfectly as **guest order**
  - Order number provided for tracking
  - Email/SMS updates still work
  - Can track order by order number and email
  - All order features work: verification, updates, cancellation, rescheduling
  - **Perfect for customers who prefer not to register**

**Total Time: ~3 minutes** (vs. 5-10 minutes on competitors)
**No registration required** - accessible to all customers, especially elderly users

#### 4.1.2 Customer Portal Features

**Dashboard:**
- Upcoming appointments (next 3)
- Quick rebook button
- Payment history
- Service history
- Account settings

**Booking Management:**
- View all appointments
- View subscriptions (recurring services)
- View orders (multi-service bookings)
- Cancel (with 24h policy)
- Reschedule (self-service)
- Request date/time changes
- Add notes/instructions
- Upload photos (before/after)

**Subscriptions:**
- Subscribe to recurring services (e.g., weekly cleaning for 3 months)
- View subscription schedule
- Manage subscription (pause, cancel, modify)
- Cancel individual subscription appointments (before 24h)
- View upcoming subscription appointments

**Orders:**
- Create orders with multiple services (e.g., window cleaning + grass cutting)
- View order status
- Request date/time changes for orders
- Cancel orders (fully before 24h)
- Track order progress

**Payment:**
- View invoices
- Pay outstanding balances
- Payment methods management
- Receipts download

**Profile:**
- Edit contact information
- Saved addresses
- Notification preferences
- Service preferences

**Calendar Sync:**
- Connect Google Calendar
- Connect Outlook Calendar
- Connect Apple Calendar (iCal/CalDAV)
- Sync appointments to personal calendar
- Add appointments to external calendars
- Two-way sync (optional)
- Download .ics files
- Calendar sync status

### 4.2 Staff Experience (Powerful Management)

#### 4.2.1 Staff Mobile App / Portal

**Today's Schedule:**
- List view of today's jobs
- Shows regular appointments, subscription appointments, and order items
- Map view with route optimization
- Job details and customer info
- Job type indicator (appointment/subscription/order)
- Navigation integration
- Check-in/Check-out
- Photo upload
- Customer signature
- Job completion status

**Job Management:**
- Accept/decline jobs
- Update job status
- Add notes
- Request assistance
- Time tracking

**Availability:**
- Set working hours
- Block unavailable times
- Request time off
- View schedule

**Performance:**
- Jobs completed
- Customer ratings
- Earnings (if applicable)
- Performance metrics

#### 4.2.2 Staff Web Portal

**Calendar View:**
- Monthly/Weekly/Daily views
- Drag-and-drop rescheduling
- Color-coded by service type
- Filter by service, customer
- Export to personal calendar

**Calendar Sync:**
- Connect Google Calendar
- Connect Outlook Calendar
- Connect Apple Calendar (iCal/CalDAV)
- Sync schedule to personal calendar
- Add custom events to external calendars
- Two-way sync (optional)
- Download .ics files
- Calendar sync status

**Customer Management:**
- Customer history
- Notes and preferences
- Contact information
- Service history

### 4.3 Manager Experience (Flexible Management)

#### 4.3.1 Manager Dashboard

**Manager Permissions (Configurable by Admin):**
- Can manage customers only
- Can manage specific staff members
- Can manage staff and customers in specific locations
- Can manage all staff and customers (full manager access)
- Custom permission sets per manager

**Manager Features:**
- View assigned customers/staff
- Manage appointments for assigned scope
- View reports for assigned scope
- Staff scheduling (if permission granted)
- Customer management (if permission granted)

**Calendar Sync:**
- Connect Google Calendar
- Connect Outlook Calendar
- Connect Apple Calendar (iCal/CalDAV)
- Sync appointments to personal calendar
- Add custom events to external calendars
- Two-way sync (optional)
- Download .ics files
- Calendar sync status

### 4.4 Admin Experience (Complete Control)

#### 4.4.1 Admin Dashboard

**Key Metrics (Real-time):**
- Today's appointments
- Revenue (today/week/month)
- Pending approvals
- Staff utilization
- Customer growth
- Conversion rate
- Average booking value

**Quick Actions:**
- Create appointment
- Add customer
- View calendar
- Process payment
- Send notification

**Recent Activity:**
- New bookings
- Completed jobs
- Payments received
- Customer registrations

#### 4.4.2 Calendar Management

**Advanced Calendar:**
- Multi-view (month/week/day)
- Drag-and-drop editing
- Bulk operations
- Filter by staff, service, status
- Color coding
- Calendar sync indicators
- Block time slots
- Recurring appointment creation

**Features:**
- Real-time updates
- Conflict detection
- Auto-assignment suggestions
- Route optimization view

**Calendar Sync:**
- Connect Google Calendar
- Connect Outlook Calendar
- Connect Apple Calendar (iCal/CalDAV)
- Sync all appointments to personal calendar
- Add custom events to external calendars
- Two-way sync (optional)
- Bulk sync operations
- Download .ics files
- Calendar sync status and management

#### 4.4.3 Staff Management

**Staff Profiles:**
- Personal information
- Photo and bio
- Service assignments
- Pricing per service
- Schedule management
- Performance metrics
- **Area/Postcode Assignment** (NEW)
  - Assign postcodes with radius (km)
  - Multiple postcode areas per staff
  - Service radius configuration
  - Area coverage map view

**Scheduling:**
- Weekly schedule editor
- Break management
- Holiday management
- Availability rules
- Calendar integration per staff

**Area Management:**
- Postcode assignment interface
- Radius configuration (km)
- Multiple areas per staff
- Area coverage visualization
- Staff availability by area

**Performance:**
- Jobs completed
- Customer ratings
- Revenue generated
- Utilization rate
- Area coverage statistics

#### 4.4.4 Customer Management

**Customer Database:**
- Search and filter
- Customer profiles
- Booking history
- Payment history
- Notes and tags
- Communication log
- Merge duplicates

**Customer Insights:**
- Lifetime value
- Booking frequency
- Preferred services
- Preferred times
- Churn risk

#### 4.4.5 Service Management

**Service Catalog:**
- Categories and services
- Pricing management
- Duration settings
- Staff assignments
- Service images
- Descriptions
- Visibility settings

**Service Analytics:**
- Popularity
- Revenue per service
- Average duration
- Customer satisfaction

#### 4.4.6 Financial Management

**Payments:**
- Payment list with filters
- Payment details
- Refund processing
- Payment methods
- Outstanding balances

**Invoicing:**
- Generate invoices
- Send invoices
- Payment reminders
- Invoice templates

**Reports:**
- Revenue reports
- Payment reports
- Service performance
- Staff performance
- Customer analytics
- Export to CSV/PDF

#### 4.4.7 Manager & Permission Management

**Manager Configuration:**
- Create/edit managers
- Assign permissions (customers, staff, locations)
- Set scope of access (all, specific locations, specific staff)
- Permission templates
- Manager hierarchy

#### 4.4.8 Settings & Configuration

**General Settings:**
- Business information
- Time zone
- Date/time formats
- Booking rules
- Cancellation policy

**Payment Settings:**
- Payment gateways
- Currency
- Deposit settings
- Tax configuration

**Notification Settings:**
- Email templates
- SMS templates
- Notification triggers
- Reminder settings

**Integration Settings:**
- Calendar integrations
- Payment gateways
- SMS provider
- Email service
- Address lookup

---

## 5. Implementation Phases

### Phase 1: Foundation (Weeks 1-3) - MVP Core

**Goal**: Basic booking system that works

**Backend:**
- ✅ Django project setup
- ✅ Database models (User, Service, Staff, Customer, Manager, Appointment)
- ✅ SQLite database for development (localhost)
- ✅ REST API endpoints
- ✅ Authentication system with role-based access (Admin, Manager, Staff, Customer)
- ✅ Basic admin panel

**Frontend:**
- ✅ Next.js project setup
- ✅ Authentication pages (login, register)
- ✅ Basic booking flow (4 steps)
- ✅ Customer dashboard
- ✅ Staff dashboard
- ✅ Manager dashboard (with permission-based views)
- ✅ Admin dashboard (basic)

**Deliverables:**
- Working booking system
- Customer can book appointments
- Admin can view/manage appointments
- Basic authentication

### Phase 2: Enhanced Booking (Weeks 4-5)

**Goal**: Professional booking experience

**Features:**
- ✅ Time slot calculation
- ✅ Multi-calendar integration (Google, Outlook, Apple) - All roles
- ✅ Calendar sync for Staff, Customer, Manager, Admin
- ✅ Custom event creation to external calendars
- ✅ Address autocomplete (Google Places API)
- ✅ Postcode-first booking flow
- ✅ Area-based service filtering
- ✅ Payment integration (Stripe)
- ✅ Email notifications
- ✅ Booking confirmation

**Deliverables:**
- Complete booking flow with payments
- Calendar sync
- Email confirmations
- Payment processing

### Phase 3: Management Tools (Weeks 6-8)

**Goal**: Powerful admin and staff tools

**Features:**
- ✅ Advanced calendar view
- ✅ Staff management
- ✅ Customer management
- ✅ Service management
- ✅ Route optimization
- ✅ Mobile-responsive admin

**Deliverables:**
- Full admin panel
- Staff portal
- Customer portal
- Management tools

### Phase 4: Advanced Features (Weeks 9-11)

**Goal**: Enterprise-level features

**Features:**
- ✅ Subscription system (recurring services)
- ✅ Order system (multi-service bookings)
- ✅ Order management (change requests, cancellation)
- ✅ Subscription management (pause, cancel, individual appointments)
- ✅ 24h cancellation policy enforcement
- ✅ Coupons and discounts
- ✅ Custom fields
- ✅ SMS notifications
- ✅ Reporting and analytics
- ✅ Customer reviews/ratings

**Deliverables:**
- Subscription system with automatic appointment generation
- Multi-service order system
- Order and subscription management
- Cancellation policy system
- Marketing tools
- Analytics dashboard
- Customer engagement features

### Phase 5: Mobile & Optimization (Weeks 12-13)

**Goal**: Mobile-first experience

**Features:**
- ✅ Progressive Web App (PWA)
- ✅ Mobile app (React Native - optional)
- ✅ Performance optimization
- ✅ SEO optimization
- ✅ Accessibility improvements

**Deliverables:**
- Mobile-optimized experience
- Fast loading times
- SEO-friendly
- Accessible to all users

### Phase 6: Polish & Launch (Weeks 14-15)

**Goal**: Production-ready system

**Tasks:**
- ✅ Comprehensive testing
- ✅ Bug fixes
- ✅ Performance tuning
- ✅ Security audit
- ✅ Documentation
- ✅ User training materials
- ✅ Launch preparation

**Deliverables:**
- Production-ready system
- Complete documentation
- Training materials
- Launch plan

---

## 6. User Journey Maps

### 6.1 Customer Booking Journey

```
1. Discovery
   └─> Finds MultiBook website
   └─> Clicks "Book Now" button

2. Postcode Entry
   └─> Enters postcode
   └─> System validates postcode
   └─> Shows available services in area
   └─> Shows service coverage map (optional)

3. Service Selection
   └─> Views services available in postcode area
   └─> Selects service (e.g., "Deep Clean")
   └─> Sees price and duration
   └─> Sees available staff in area

4. Scheduling
   └─> Views calendar
   └─> Selects date
   └─> Selects time slot (only staff in area shown)
   └─> Confirms selection

5. Guest Details Entry (NO LOGIN/REGISTRATION REQUIRED)
   └─> Enters name and email
   └─> Enters phone number
   └─> Enters address (Google Places autocomplete)
   └─> Address auto-filled from postcode
   └─> Adds special instructions (optional)
   └─> **Guest checkout** - no account creation needed
   └─> Perfect for elderly customers who don't want to register

6. Payment
   └─> Reviews booking summary
   └─> Selects payment method
   └─> Enters payment details
   └─> Confirms payment
   └─> **No login required** - payment works for guests

7. Order Confirmation (Guest Order Created)
   └─> Receives confirmation email
   └─> Receives SMS reminder (optional)
   └─> Downloads calendar file
   └─> Receives order number for tracking
   └─> **Guest order fully functional** - all features work

8. Post-Order Account Linking (OPTIONAL - Customer Choice)
   
   **Scenario A: Customer has existing account (email match)**
   └─> System detects email exists in database
   └─> Shows prompt: "Login to link this order to your account?"
   └─> Customer clicks "Login"
   └─> Login modal opens with email pre-filled
   └─> Customer enters password
   └─> Order automatically linked to account
   └─> Customer can now manage order from dashboard
   └─> **OR** Customer clicks "Skip" - order remains as guest order
   
   **Scenario B: Customer doesn't have account (new email)**
   └─> System detects email not in database
   └─> Shows prompt: "Create an account to manage your orders? (Optional)"
   └─> Benefits shown: "Track orders, view history, faster rebooking"
   └─> Customer can click "Create Account" (pre-filled details)
   └─> One-click registration (name, email, phone already filled)
   └─> Order automatically linked to new account
   └─> **OR** Customer clicks "Skip" - order remains as guest order
   
   **Scenario C: Customer doesn't want to register (elderly-friendly)**
   └─> Customer clicks "Skip" or closes the prompt
   └─> **Guest order continues to work perfectly**
   └─> Order tracking by order number and email
   └─> All features work: verification, updates, cancellation, rescheduling
   └─> Email/SMS notifications work
   └─> Customer can access order via email link or order number lookup
   └─> **Perfect for customers who prefer not to register**

9. Guest Order Management (Works Without Account)
   └─> Customer receives order number
   └─> Can track order via email link (no login required)
   └─> Can request date/time changes (via email link)
   └─> Can cancel (before 24h deadline, via email link)
   └─> Receives all notifications via email/SMS
   └─> All order features work as guest order
   └─> **Elderly-friendly** - simple email-based access

10. Account-Based Order Management (If Linked to Account)
   └─> If order was linked to account: Can manage from dashboard
   └─> Can request date/time changes (orders)
   └─> Can cancel (before 24h deadline)
   └─> Can pause subscription (if applicable)
   └─> Can cancel individual subscription appointments (before 24h)
   └─> Views upcoming appointments from subscriptions
   └─> Full dashboard access

9. Service Day
   └─> Receives reminder (24h before)
   └─> Staff arrives
   └─> Service completed
   └─> Receives completion notification
   └─> If subscription: Next appointment scheduled automatically

10. Post-Service
   └─> Receives invoice
   └─> Can leave review
   └─> Can rebook easily
   └─> If subscription: Views progress and remaining appointments
```

### 6.2 Staff Workflow Journey

```
1. Start of Day
   └─> Opens staff app/portal
   └─> Views today's schedule
   └─> Sees regular appointments, subscription appointments, and order items
   └─> Job type indicators (appointment/subscription/order)
   └─> Reviews route optimization
   └─> Prepares for first job

2. Job Execution
   └─> Navigates to customer location
   └─> Checks in (GPS location)
   └─> Reviews job details (shows if subscription or order item)
   └─> Performs service
   └─> Takes photos (before/after)
   └─> Gets customer signature
   └─> Marks job complete
   └─> If subscription appointment: Next one automatically scheduled
   └─> Checks out

3. Between Jobs
   └─> Views next job
   └─> Navigates to next location
   └─> Updates status if needed

4. End of Day
   └─> Reviews completed jobs
   └─> Updates availability if needed
   └─> Views performance metrics
```

### 6.3 Admin Management Journey

```
1. Daily Overview
   └─> Logs into admin dashboard
   └─> Reviews key metrics
   └─> Checks pending approvals
   └─> Reviews today's schedule

2. Schedule Management
   └─> Views calendar
   └─> Assigns staff to jobs
   └─> Adjusts schedules as needed
   └─> Handles cancellations

3. Customer Management
   └─> Responds to customer inquiries
   └─> Updates customer information
   └─> Reviews customer history
   └─> Manages customer relationships

4. Financial Management
   └─> Reviews payments
   └─> Processes refunds if needed
   └─> Generates invoices
   └─> Reviews financial reports

5. Business Optimization
   └─> Reviews analytics
   └─> Identifies trends
   └─> Makes data-driven decisions
   └─> Adjusts services/pricing
```

---

## 7. Technical Specifications

### 7.1 Database Schema (Key Models)

#### User & Authentication
```python
User (extends Django User)
- email, username
- role (admin, manager, staff, customer)
- is_active, is_verified
- created_at, updated_at

Profile
- user (OneToOne)
- phone, avatar
- timezone
- preferences (JSON)
- calendar_sync_enabled (boolean)
- calendar_provider (enum: google, outlook, apple, none)
- calendar_access_token (encrypted, nullable)
- calendar_refresh_token (encrypted, nullable)
- calendar_calendar_id (string, nullable)
- calendar_sync_settings (JSON) - sync preferences

Manager (extends User)
- user (OneToOne)
- permissions (JSON) - stores permission configuration
- managed_locations (M2M, if location-based)
- managed_staff (M2M, if staff management enabled)
- managed_customers (M2M, if customer management enabled)
- can_manage_all (boolean)
```

#### Services
```python
Category
- name, slug, description
- image, position
- is_active

Service
- category (FK)
- name, slug, description
- duration (minutes)
- price, currency
- image, color
- capacity, padding_time
- is_active, position
```

#### Staff
```python
Staff
- user (FK, nullable)
- name, email, phone
- photo, bio
- services (M2M)
- is_active
# Note: Calendar sync now handled in Profile model for all users

StaffSchedule
- staff (FK)
- day_of_week (0-6)
- start_time, end_time
- breaks (JSON)

StaffService
- staff (FK), service (FK)
- price_override
- duration_override

StaffArea
- staff (FK)
- postcode (string) - center postcode
- radius_km (decimal) - service radius in kilometers
- is_active (boolean)
- created_at, updated_at
```

#### Customers
```python
Customer
- user (FK, nullable)
- name, email, phone
- address fields
- address_validated
- notes, tags
- created_at

Address
- customer (FK)
- type (billing, service)
- address fields
- is_default
```

#### Appointments
```python
Appointment
- staff (FK)
- service (FK)
- start_time, end_time
- status (pending, confirmed, completed, cancelled)
- appointment_type (enum: single, subscription, order_item)
- subscription (FK, nullable) - if part of subscription
- order (FK, nullable) - if part of order
- calendar_event_id (JSON) - stores event IDs for each provider
- calendar_synced_to (JSON) - tracks which calendars event is synced to
- location (FK, if multi-location)
- internal_notes

CustomerAppointment
- customer (FK)
- appointment (FK)
- number_of_persons
- extras (JSON)
- custom_fields (JSON)
- total_price
- deposit_paid
- payment_status
- cancellation_token
- can_cancel (boolean) - based on 24h policy
- can_reschedule (boolean) - based on 24h policy
- cancellation_deadline (datetime) - 24h before appointment
```

#### Subscriptions (Guest Checkout Support)
```python
Subscription
- customer (FK, nullable) - NULL for guest subscriptions, linked after login/registration
- guest_email (string, nullable) - Email for guest subscriptions (required if customer is NULL)
- guest_name (string, nullable) - Name for guest subscriptions
- guest_phone (string, nullable) - Phone for guest subscriptions
- subscription_number (string, unique) - Similar to order_number
- tracking_token (string, unique) - For guest subscription access via email link
- is_guest_subscription (boolean, default: False) - Flag for guest subscriptions
- account_linked_at (datetime, nullable) - When guest subscription was linked to account
- service (FK)
- staff (FK, nullable) - preferred staff
- frequency (enum: weekly, biweekly, monthly)
- duration_months (integer) - subscription duration (1, 2, 3, 6, 12)
- start_date (date)
- end_date (date, calculated)
- next_appointment_date (date)
- status (active, paused, cancelled, completed)
- total_appointments (integer) - calculated
- completed_appointments (integer)
- price_per_appointment (decimal)
- total_price (decimal)
- payment_status (enum)
- cancellation_policy_hours (integer, default: 24)
- address_line1, address_line2, city, postcode, country - Guest address
- created_at, updated_at

# Guest Subscription Access
- Subscriptions can be accessed via:
  1. Subscription number + email (for guests)
  2. Tracking token (unique link sent via email)
  3. Customer account (if linked)

SubscriptionAppointment
- subscription (FK)
- appointment (FK)
- sequence_number (integer)
- scheduled_date (date)
- status (scheduled, completed, cancelled, skipped)
- can_cancel (boolean) - based on 24h policy
- cancellation_deadline (datetime)
```

#### Orders (Guest Checkout Support)
```python
Order
- customer (FK, nullable) - NULL for guest orders, linked after login/registration
- guest_email (string, nullable) - Email for guest orders (required if customer is NULL)
- guest_name (string, nullable) - Name for guest orders
- guest_phone (string, nullable) - Phone for guest orders
- order_number (string, unique)
- tracking_token (string, unique) - For guest order access via email link
- is_guest_order (boolean, default: False) - Flag for guest orders
- account_linked_at (datetime, nullable) - When guest order was linked to account
- status (pending, confirmed, in_progress, completed, cancelled)
- total_price (decimal)
- deposit_paid (decimal)
- payment_status (enum)
- scheduled_date (date) - preferred date
- scheduled_time (time, nullable) - preferred time
- cancellation_policy_hours (integer, default: 24)
- can_cancel (boolean) - based on 24h policy
- can_reschedule (boolean) - based on 24h policy
- cancellation_deadline (datetime)
- address_line1, address_line2, city, postcode, country - Guest address
- created_at, updated_at

# Guest Order Access
- Orders can be accessed via:
  1. Order number + email (for guests)
  2. Tracking token (unique link sent via email)
  3. Customer account (if linked)
```

**Note:** When customer links guest order to account:
- `customer` FK is set
- `is_guest_order` remains True (historical record)
- `account_linked_at` is set
- Order becomes accessible from customer dashboard
- Guest email/name/phone preserved for records

OrderItem
- order (FK)
- service (FK)
- staff (FK, nullable) - assigned staff
- appointment (FK, nullable) - created appointment
- quantity (integer, default: 1)
- price (decimal)
- status (pending, scheduled, completed, cancelled)
- notes (text, nullable)
```

#### Payments
```python
Payment
- customer_appointment (FK)
- amount, currency
- payment_method
- status (pending, completed, failed, refunded)
- transaction_id
- gateway_response (JSON)
- created_at

Invoice
- customer (FK)
- appointments (M2M)
- total_amount
- tax_amount
- status (draft, sent, paid, overdue)
- due_date
```

### 7.2 API Endpoints Structure

**Security Note:** ALL endpoints (both public and protected) use shortened prefixes for security to prevent enumeration attacks.

**Public Endpoints (Security Prefixes):**
- Services: `/api/svc/` (instead of `/api/services/`)
- Staff (public listing): `/api/stf/` (instead of `/api/staff/`)
- Bookings: `/api/bkg/` (instead of `/api/bookings/`)
- Address: `/api/addr/` (instead of `/api/address/`)
- Auth: `/api/aut/` (instead of `/api/auth/`)
- Slots: `/api/slots/` (instead of `/api/available-slots/`)

**Protected Endpoints (Role-Based Security Prefixes):**
- Customer: `/api/cus/` (instead of `/api/customer/`)
- Staff (protected): `/api/st/` (instead of `/api/staff/`)
- Manager: `/api/man/` (instead of `/api/manager/`)
- Admin: `/api/ad/` (instead of `/api/admin/`)

This makes endpoints less predictable and harder to enumerate, improving security posture.

#### Public Endpoints (Guest Checkout Supported)
```
GET  /api/svc/                      # List services (filtered by postcode)
GET  /api/svc/{id}/                 # Service details
GET  /api/svc/by-postcode/          # Get services available in postcode area
GET  /api/stf/                      # List staff (filtered by postcode/area)
GET  /api/stf/by-postcode/          # Get staff available in postcode area
GET  /api/slots/                    # Get available time slots (for postcode area)

# Booking/Order/Subscription Creation (Guest Checkout - NO AUTH REQUIRED)
POST /api/bkg/                      # Create single appointment (guest checkout supported)
POST /api/bkg/subscription/         # Create subscription (guest checkout supported)
POST /api/bkg/order/                # Create multi-service order (guest checkout supported)

# Guest Order Access (NO AUTH REQUIRED)
GET  /api/bkg/guest/order/{order_number}/        # Get guest order by order number
POST /api/bkg/guest/order/{order_number}/verify/ # Verify guest order access (email + order number)
GET  /api/bkg/guest/order/track/{tracking_token}/ # Track guest order by tracking token
POST /api/bkg/guest/order/{order_number}/cancel/  # Cancel guest order (24h policy)
POST /api/bkg/guest/order/{order_number}/request-change/ # Request date/time change (guest)

# Guest Subscription Access (NO AUTH REQUIRED)
GET  /api/bkg/guest/subscription/{subscription_number}/     # Get guest subscription by number
POST /api/bkg/guest/subscription/{subscription_number}/verify/ # Verify guest subscription access
GET  /api/bkg/guest/subscription/track/{tracking_token}/     # Track guest subscription by token
POST /api/bkg/guest/subscription/{subscription_number}/pause/  # Pause guest subscription
POST /api/bkg/guest/subscription/{subscription_number}/cancel/ # Cancel guest subscription
POST /api/bkg/guest/subscription/{subscription_number}/appointments/{appt_id}/cancel/ # Cancel subscription appointment

# Account Linking (After Order/Subscription Completion - OPTIONAL)
POST /api/bkg/guest/check-email/                  # Check if email matches existing account (for prompt)
POST /api/bkg/guest/order/{order_number}/link-login/     # Link guest order to account (login required)
POST /api/bkg/guest/order/{order_number}/link-register/  # Link guest order to account (registration)
POST /api/bkg/guest/subscription/{subscription_number}/link-login/     # Link guest subscription to account
POST /api/bkg/guest/subscription/{subscription_number}/link-register/  # Link guest subscription to account

# Address & Authentication
POST /api/addr/autocomplete/        # Google Places API autocomplete
POST /api/aut/register/             # Register (optional, for account creation)
POST /api/aut/login/                # Login (optional, for account linking)
POST /api/aut/check-email/          # Check if email exists (for account linking prompt)
```

#### Customer Endpoints (Security: /api/cus/)
```
GET  /api/cus/appointments/     # My appointments
GET  /api/cus/appointments/{id}/ # Appointment details
POST /api/cus/appointments/{id}/cancel/ # Cancel (if allowed)
POST /api/cus/appointments/{id}/reschedule/ # Reschedule (if allowed)
GET  /api/cus/invoices/         # My invoices
GET  /api/cus/profile/          # My profile
PUT  /api/cus/profile/          # Update profile

# Subscriptions
GET  /api/cus/subscriptions/                    # My subscriptions
POST /api/cus/subscriptions/                    # Create subscription
GET  /api/cus/subscriptions/{id}/               # Subscription details
PUT  /api/cus/subscriptions/{id}/               # Update subscription
POST /api/cus/subscriptions/{id}/pause/         # Pause subscription
POST /api/cus/subscriptions/{id}/cancel/        # Cancel subscription
POST /api/cus/subscriptions/{id}/appointments/{appt_id}/cancel/ # Cancel subscription appointment

# Orders
GET  /api/cus/orders/                          # My orders
POST /api/cus/orders/                         # Create order (multi-service)
GET  /api/cus/orders/{id}/                      # Order details
POST /api/cus/orders/{id}/request-change/       # Request date/time change
POST /api/cus/orders/{id}/cancel/               # Cancel order (if allowed)
GET  /api/cus/orders/{id}/status/               # Order status

# Calendar Sync
POST /api/cus/calendar/connect/        # Connect calendar (Google/Outlook/Apple)
GET  /api/cus/calendar/status/         # Get calendar sync status
POST /api/cus/calendar/sync/           # Sync appointments to calendar
POST /api/cus/calendar/disconnect/     # Disconnect calendar
GET  /api/cus/calendar/events/         # Get synced events
POST /api/cus/calendar/add-event/      # Add custom event to calendar
```

#### Staff Endpoints (Security: /api/st/)
```
GET  /api/st/schedule/            # My schedule
GET  /api/st/jobs/                # My jobs
POST /api/st/jobs/{id}/checkin/   # Check in
POST /api/st/jobs/{id}/complete/  # Complete job
GET  /api/st/availability/        # My availability
PUT  /api/st/availability/        # Update availability

# Calendar Sync
POST /api/st/calendar/connect/        # Connect calendar (Google/Outlook/Apple)
GET  /api/st/calendar/status/         # Get calendar sync status
POST /api/st/calendar/sync/           # Sync schedule to calendar
POST /api/st/calendar/disconnect/     # Disconnect calendar
GET  /api/st/calendar/events/         # Get synced events
POST /api/st/calendar/add-event/      # Add custom event to calendar
```

#### Manager Endpoints (Security: /api/man/)
```
# Appointments (within scope)
GET    /api/man/appointments/
POST   /api/man/appointments/
PUT    /api/man/appointments/{id}/
DELETE /api/man/appointments/{id}/

# Staff (if permission granted)
GET    /api/man/staff/
PUT    /api/man/staff/{id}/

# Customers (if permission granted)
GET    /api/man/customers/
GET    /api/man/customers/{id}/
PUT    /api/man/customers/{id}/

# Reports (within scope)
GET    /api/man/reports/revenue/
GET    /api/man/reports/appointments/

# Calendar Sync
POST   /api/man/calendar/connect/        # Connect calendar (Google/Outlook/Apple)
GET    /api/man/calendar/status/         # Get calendar sync status
POST   /api/man/calendar/sync/           # Sync appointments to calendar
POST   /api/man/calendar/disconnect/     # Disconnect calendar
GET    /api/man/calendar/events/         # Get synced events
POST   /api/man/calendar/add-event/      # Add custom event to calendar
```

#### Admin Endpoints (Security: /api/ad/)
```
# Appointments
GET    /api/ad/appointments/
POST   /api/ad/appointments/
PUT    /api/ad/appointments/{id}/
DELETE /api/ad/appointments/{id}/

# Staff
GET    /api/ad/staff/
POST   /api/ad/staff/
PUT    /api/ad/staff/{id}/
DELETE /api/ad/staff/{id}/

# Customers
GET    /api/ad/customers/
GET    /api/ad/customers/{id}/
PUT    /api/ad/customers/{id}/

# Managers
GET    /api/ad/managers/
POST   /api/ad/managers/
PUT    /api/ad/managers/{id}/
DELETE /api/ad/managers/{id}/
PUT    /api/ad/managers/{id}/permissions/  # Set manager permissions

# Services
GET    /api/ad/services/
POST   /api/ad/services/
PUT    /api/ad/services/{id}/
DELETE /api/ad/services/{id}/

# Subscriptions
GET    /api/ad/subscriptions/
GET    /api/ad/subscriptions/{id}/
PUT    /api/ad/subscriptions/{id}/
POST   /api/ad/subscriptions/{id}/cancel/
GET    /api/ad/subscriptions/{id}/appointments/

# Orders
GET    /api/ad/orders/
GET    /api/ad/orders/{id}/
PUT    /api/ad/orders/{id}/
POST   /api/ad/orders/{id}/approve-change/  # Approve date/time change request
POST   /api/ad/orders/{id}/cancel/
GET    /api/ad/orders/{id}/items/

# Reports
GET    /api/ad/reports/revenue/
GET    /api/ad/reports/appointments/
GET    /api/ad/reports/staff-performance/
GET    /api/ad/reports/subscriptions/      # Subscription analytics
GET    /api/ad/reports/orders/             # Order analytics

# Calendar Sync
POST   /api/ad/calendar/connect/        # Connect calendar (Google/Outlook/Apple)
GET    /api/ad/calendar/status/         # Get calendar sync status
POST   /api/ad/calendar/sync/           # Sync all appointments to calendar
POST   /api/ad/calendar/disconnect/     # Disconnect calendar
GET    /api/ad/calendar/events/         # Get synced events
POST   /api/ad/calendar/add-event/      # Add custom event to calendar
POST   /api/ad/calendar/bulk-sync/      # Bulk sync operations
```

### 7.3 Frontend Component Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes
│   │   ├── login/
│   │   └── register/
│   ├── cus/                # Customer routes (Security: /cus/)
│   │   ├── dashboard/
│   │   ├── bookings/
│   │   ├── subscriptions/
│   │   ├── orders/
│   │   └── profile/
│   ├── st/                 # Staff routes (Security: /st/)
│   │   ├── dashboard/
│   │   ├── schedule/
│   │   └── jobs/
│   ├── man/                # Manager routes (Security: /man/)
│   │   ├── dashboard/
│   │   ├── calendar/
│   │   ├── appointments/
│   │   ├── staff/         # If permission granted
│   │   ├── customers/     # If permission granted
│   │   └── reports/
│   ├── ad/                 # Admin routes (Security: /ad/)
│   │   ├── dashboard/
│   │   ├── calendar/
│   │   ├── appointments/
│   │   ├── staff/
│   │   ├── customers/
│   │   ├── managers/      # Manager management
│   │   └── settings/
│   ├── booking/           # Public booking
│   │   ├── step1/
│   │   ├── step2/
│   │   ├── step3/
│   │   └── step4/
│   └── api/               # API routes (if needed)
│
├── components/            # Reusable components
│   ├── ui/               # shadcn/ui components
│   ├── booking/          # Booking-specific
│   ├── calendar/         # Calendar components
│   └── forms/            # Form components
│
├── lib/                  # Utilities
│   ├── api/              # API client
│   ├── utils/            # Helper functions
│   └── hooks/            # Custom hooks
│
├── store/                # State management
│   └── booking-store.ts
│
└── types/                # TypeScript types
    └── index.ts
```

### 7.4 Security Considerations

**Authentication:**
- JWT tokens with refresh tokens
- Secure password hashing (bcrypt)
- Two-factor authentication (optional)
- Social login (OAuth 2.0)

**Authorization:**
- Role-based access control (RBAC): Admin, Manager, Staff, Customer
- Manager permissions (configurable by admin)
- Permission-based endpoints
- Row-level security (managers see only assigned scope)

**Data Protection:**
- HTTPS everywhere
- Data encryption at rest
- PII data encryption
- GDPR compliance
- Regular security audits

**API Security:**
- Rate limiting
- CORS configuration
- Input validation
- SQL injection prevention
- XSS prevention
- CSRF protection

---

## 8. Success Metrics

### 8.1 User Experience Metrics

**Customer Metrics:**
- Booking completion rate: > 80%
- Average booking time: < 3 minutes
- Customer satisfaction score: > 4.5/5
- Repeat booking rate: > 60%
- Mobile booking rate: > 70%

**Staff Metrics:**
- Job completion rate: > 95%
- On-time arrival rate: > 90%
- Staff satisfaction: > 4.0/5
- App usage rate: > 80%

**Admin Metrics:**
- Dashboard usage: Daily active admins
- Time saved: > 50% vs manual process
- Error reduction: > 80%
- Report generation time: < 5 seconds

### 8.2 Technical Metrics

**Performance:**
- Page load time: < 2 seconds
- API response time: < 200ms (p95)
- Uptime: > 99.9%
- Error rate: < 0.1%

**Scalability:**
- Support 1000+ concurrent users
- Handle 10,000+ bookings/month
- Database query time: < 100ms (p95)

### 8.3 Business Metrics

**Revenue:**
- Online booking conversion: > 15%
- Payment success rate: > 98%
- Average booking value
- Revenue growth rate

**Operations:**
- Booking volume
- Staff utilization rate
- Customer acquisition cost
- Customer lifetime value

---

## 9. Next Steps

### Immediate Actions (Week 1)

1. **Technology Stack Confirmed** ✅
   - ✅ Next.js 14+ for frontend (localhost:3000)
   - ✅ Django 5.0+ for backend (localhost:8000)
   - ✅ SQLite for development database
   - ✅ Set up development environment

2. **Design System**
   - Create UI/UX mockups
   - Define color scheme and branding
   - Create component library

3. **Project Setup**
   - Initialize Django project
   - Initialize Next.js project
   - Set up database
   - Configure development tools

4. **Team Alignment**
   - Review this document
   - Assign roles and responsibilities
   - Set up communication channels
   - Define sprint structure

### Documentation to Create

1. **API Documentation** - OpenAPI/Swagger specs
2. **Component Library** - Storybook documentation
3. **User Guides** - For customers, staff, admins
4. **Developer Guide** - Setup and contribution
5. **Deployment Guide** - Production deployment
6. **Security Guide** - Security best practices

---

## 10. Conclusion

This solution combines the best features from HouseCallPro and Bookly, tailored specifically for MultiBook's cleaning services business. The system is designed to be:

- **Easy for customers** - Simple 4-step booking process
- **Powerful for staff** - Complete mobile and web tools
- **Efficient for admins** - Comprehensive management and analytics

**Key Differentiators:**
1. ⚡ **Fast Booking** - 2.5 minutes vs. 5-10 minutes
2. 🛒 **Guest Checkout** - No login/registration required - Perfect for elderly customers
3. 🔗 **Optional Account Linking** - Link orders to account after completion (customer choice)
4. 📱 **Mobile-First** - Works perfectly on all devices
5. 🎯 **Location-Based** - Postcode-first booking with area-based service filtering
6. 🚀 **Modern Stack** - Next.js + Django = Best performance
7. 💼 **Enterprise Features** - Route optimization, analytics, reporting
8. 🔒 **Secure** - Bank-level security
9. 📊 **Data-Driven** - Comprehensive analytics

**Estimated Timeline:** 15 weeks to production-ready MVP
**Team Size:** 2-3 developers (1 full-stack, 1 frontend, 1 backend)
**Budget:** Development + Third-party services (Stripe, Twilio, etc.)

---

*This document is a living document and will be updated as requirements evolve.*

**Last Updated:** [Current Date]
**Version:** 1.0
**Status:** Planning Phase

