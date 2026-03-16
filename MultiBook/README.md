# MultiBook — Multi-Service Booking System

**Status: ✅ Complete | Production-ready**

A comprehensive, enterprise-grade appointment booking system combining the best features from HouseCallPro and Bookly. Built for any service business — cleaning, labour, garden, handy work, property boards, housing associations.

**Tech Stack:** Django REST + Next.js | PostgreSQL (Supabase) | AWS deployment

**Built for:** Cleaning • Maintenance • Landscaping • Handyman • Labour • Property boards • Housing associations • Any service business from solo to enterprise.

---

## 🎯 Project Status: Complete

All core features implemented, tested, and deployed. 35 database tables, 80 CHECK constraints, 43 migrations. Production on AWS.

---

## ✅ Features Implemented

### Booking & Orders
- ✅ Multi-step booking workflow (8 steps)
- ✅ Multi-service orders (multiple services per order)
- ✅ Guest checkout (no account required)
- ✅ Order management (change requests, 24h cancellation policy)
- ✅ Postcode-first booking with service area radius
- ✅ Time slot availability checking
- ✅ Session-based booking flow

### Subscriptions
- ✅ Recurring services (weekly, biweekly, monthly)
- ✅ 1–12 month subscription plans
- ✅ Auto-generated appointments
- ✅ Subscription change requests (reschedule, cancel)
- ✅ Completed vs total appointment tracking

### Staff & Services
- ✅ Staff and service management (full CRUD)
- ✅ Staff schedules and availability
- ✅ Staff service areas (postcode + radius mapping)
- ✅ Service categories with extras/add-ons
- ✅ Staff-service assignments with price/duration overrides

### Customers & Accounts
- ✅ Customer management with addresses
- ✅ Role-based authentication (Admin, Manager, Staff, Customer)
- ✅ Role-based dashboards (Admin, Manager, Staff, Customer)
- ✅ Invitation system for staff/manager onboarding
- ✅ Manager-scoped access (managed staff and customers)
- ✅ Profile management (timezone, avatar, calendar sync)

### Coupons & Promotions
- ✅ Coupon system (percentage or fixed discount)
- ✅ Usage limits (max uses, max per customer)
- ✅ Minimum order amount
- ✅ Applicable/excluded services
- ✅ Valid from/until dates
- ✅ Usage tracking and reporting

### Calendar Integration
- ✅ Google Calendar OAuth sync (customer, staff, manager)
- ✅ Microsoft Outlook Calendar sync
- ✅ Apple Calendar (.ics export)
- ✅ Auto-sync on order confirmation
- ✅ Custom event creation to external calendars

### Data & Infrastructure
- ✅ 80 database CHECK constraints (data integrity)
- ✅ Query optimization (select_related, prefetch_related)
- ✅ Supabase storage for completion photos
- ✅ HTTPS enforcement (production)
- ✅ AWS deployment (EC2, PostgreSQL)
- ✅ Sample data creation command

---

## 📁 Project Structure

```
MultiBook/
├── backend/                 # Django REST API
│   ├── config/              # Settings (base, development, production)
│   ├── apps/
│   │   ├── core/            # Utilities, storage, postcode utils
│   │   ├── accounts/        # User, Profile, Manager, Invitation
│   │   ├── services/        # Category, Service (with extras)
│   │   ├── staff/           # Staff, Schedule, Service, Area
│   │   ├── customers/       # Customer, Address
│   │   ├── appointments/   # Appointment, CustomerAppointment
│   │   ├── orders/          # Order, OrderItem, ChangeRequest
│   │   ├── subscriptions/   # Subscription, SubscriptionAppointment
│   │   ├── coupons/         # Coupon, CouponUsage
│   │   ├── calendar_sync/   # Google, Outlook, Apple Calendar
│   │   ├── payments/        # Payment processing (structure)
│   │   ├── notifications/   # Email/SMS (structure)
│   │   ├── reports/         # Revenue and reporting
│   │   └── api/             # REST API endpoints
│   ├── manage.py
│   └── requirements.txt
├── frontend/                # Next.js
│   ├── app/                 # App router pages
│   ├── components/
│   └── package.json
├── docs/                    # Documentation
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- PostgreSQL (production) or SQLite (development)
- Redis (optional for development, required for production)

### 2. Installation

```bash
# Clone or navigate to the project directory
cd MultiBook

# Backend
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in `backend/` (copy from `.env.example`):

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development, or PostgreSQL/Supabase URL for production)
DATABASE_URL=sqlite:///db.sqlite3

# Supabase (for storage, optional in dev)
# SUPABASE_URL=...
# SUPABASE_KEY=...

# Add other API keys as needed
```

### 4. Database Setup

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

**Default Admin Credentials (Development):**
- **Username:** `admin`
- **Email:** `admin@yourdomain.com`
- **Password:** `*******`
- **Admin Panel:** http://localhost:8000/admin/

**⚠️ Important:** Change the admin password in production!

### 5. Create Sample Data (Optional)

```bash
# Create sample services, staff, customers, and appointments
python manage.py create_sample_data
```

This will create:
- 3 Categories (Cleaning Services, Maintenance Services, Green Spaces)
- 7 Services (multi-service booking)
- 3 Staff members with schedules
- 3 Test users/customers
- 5 Sample appointments

### 6. Run Development Server

**Backend (Django):**
```bash
cd backend
# Activate venv first:
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
python manage.py runserver
```
Backend: `http://localhost:8000`

**Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:3000`

### 8. Access the Application

**Frontend (Next.js) — http://localhost:3000**
- Home, Booking, Login
- **Customer Dashboard** `/cus/dashboard/`
- **Staff Dashboard** `/st/dashboard/`
- **Manager Dashboard** `/man/dashboard/`
- **Admin Dashboard** `/ad/dashboard/` (includes coupons, orders, staff, services)

**Backend (Django) — http://localhost:8000**
- **API** `/api/`
- **Admin Panel** `/admin/`
- **API Docs** `/api/docs/`

### 9. Production Deployment

See **[docs/AWS_DEPLOYMENT_GUIDE.md](docs/AWS_DEPLOYMENT_GUIDE.md)** for full deployment steps. The system is deployed on AWS with PostgreSQL (Supabase), Gunicorn, Nginx, and HTTPS.

## Documentation

### 🎯 Solution & Architecture
- **[docs/MULTIBOOK_BEST_SOLUTION.md](docs/MULTIBOOK_BEST_SOLUTION.md)** - Complete professional solution (HouseCallPro + Bookly features)
- **[docs/SOLUTION_OVERVIEW.md](docs/SOLUTION_OVERVIEW.md)** - Quick start guide and overview
- **[docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)** - Implementation guide
- **[docs/FEATURE_COMPARISON.md](docs/FEATURE_COMPARISON.md)** - Competitive analysis
- **[docs/TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md)** - Technical architecture

### 🚀 Deployment & Operations
- **[docs/AWS_DEPLOYMENT_GUIDE.md](docs/AWS_DEPLOYMENT_GUIDE.md)** - Step-by-step AWS deployment
- **[docs/AWS_MIGRATION_VERIFICATION.md](docs/AWS_MIGRATION_VERIFICATION.md)** - Migration verification
- **[docs/MIGRATIONS_APPLIED_SUMMARY.md](docs/MIGRATIONS_APPLIED_SUMMARY.md)** - Database constraints summary

### 📊 Database & Technical
- **[docs/DATABASE_OPERATIONS_SUMMARY.md](docs/DATABASE_OPERATIONS_SUMMARY.md)** - Database operations reference
- **[docs/DATABASE_TABLES_AUDIT.md](docs/DATABASE_TABLES_AUDIT.md)** - Table audit (35 tables)
- **[docs/COUPONS.md](docs/COUPONS.md)** - Coupon system documentation

### 📅 Calendar & Integrations
- **[docs/GOOGLE_CALENDAR_SETUP_GUIDE.md](docs/GOOGLE_CALENDAR_SETUP_GUIDE.md)** - Google Calendar OAuth setup
- **[docs/GOOGLE_CALENDAR_QUICK_START.md](docs/GOOGLE_CALENDAR_QUICK_START.md)** - Quick start for calendar sync

### 📋 Setup & Other
- **[docs/PROJECT_SETUP.md](docs/PROJECT_SETUP.md)** - Project setup instructions
- **[docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)** - Supabase configuration
- **[docs/OPTIMIZATION_COMPLETE.md](docs/OPTIMIZATION_COMPLETE.md)** - Query & constraint optimization
- **[docs/BOOKING_PERFORMANCE_OPTIMIZATION.md](docs/BOOKING_PERFORMANCE_OPTIMIZATION.md)** - Booking performance notes

---

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for full text.

