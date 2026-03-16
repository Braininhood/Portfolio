# MultiBook - Django Backend

## Overview

This is the Django backend for the MultiBook multi-service booking system. It provides RESTful API endpoints with security-focused shortened prefixes.

## Project Structure

```
backend/
├── config/                 # Django project settings
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Development settings (SQLite)
│   │   └── production.py  # Production settings (PostgreSQL)
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
│
├── apps/                   # Django apps
│   ├── core/              # Core utilities, permissions, exceptions
│   ├── api/               # API URL routing
│   ├── accounts/          # User authentication and profiles
│   ├── services/          # Services and categories
│   ├── staff/             # Staff management
│   ├── customers/         # Customer management
│   ├── appointments/      # Booking system
│   ├── payments/          # Payment processing
│   ├── subscriptions/     # Recurring subscriptions
│   ├── orders/            # Multi-service orders (guest checkout)
│   ├── notifications/     # Email/SMS notifications
│   └── calendar_sync/     # Calendar integration
│
├── static/                # Static files
├── media/                 # Media files (user uploads)
├── logs/                  # Log files
├── db.sqlite3            # SQLite database (development)
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── env.example           # Environment variables template
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `env.example` to `.env` and update the values:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Generate a SECRET_KEY:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Update `.env` with the generated SECRET_KEY.

### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

## API Endpoints

### Public Endpoints (No Authentication Required)

- `/api/v1/svc/` - Services (Security prefix: /api/svc/)
- `/api/v1/stf/` - Staff listing (Security prefix: /api/stf/)
- `/api/v1/bkg/` - Bookings/Orders (Security prefix: /api/bkg/)
- `/api/v1/addr/` - Address autocomplete (Security prefix: /api/addr/)
- `/api/v1/aut/` - Authentication (Security prefix: /api/aut/)
- `/api/v1/slots/` - Available slots (Security prefix: /api/slots/)
- `/api/v1/pay/` - Payments (Security prefix: /api/pay/)

### Protected Endpoints (Authentication Required)

- `/api/v1/cus/` - Customer endpoints (Security prefix: /api/cus/)
- `/api/v1/st/` - Staff endpoints (Security prefix: /api/st/)
- `/api/v1/man/` - Manager endpoints (Security prefix: /api/man/)
- `/api/v1/ad/` - Admin endpoints (Security prefix: /api/ad/)

### API Documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- API Schema: `http://localhost:8000/api/schema/`

## Key Features

- ✅ **Guest Checkout Support** - No login required for bookings
- ✅ **Security Prefixes** - Shortened API endpoints for security
- ✅ **JWT Authentication** - Token-based authentication
- ✅ **Role-Based Access Control** - Admin, Manager, Staff, Customer roles
- ✅ **SQLite Development** - Easy local development setup
- ✅ **CORS Configured** - For Next.js frontend on localhost:3000

## Development Notes

- **Database**: SQLite (db.sqlite3) for development
- **Settings**: Uses `config.settings.development` by default
- **CORS**: Configured for `http://localhost:3000`
- **JWT**: Access tokens expire in 15 minutes, refresh tokens in 7 days

## Next Steps

Follow the IMPLEMENTATION_ROADMAP.md for:
- Week 1 Day 5: Create database models
- Week 2: Authentication system
- Week 3: Basic booking flow
- And so on...

## Documentation

See the main project documentation:
- `../MULTIBOOK_BEST_SOLUTION.md` - Complete solution
- `../IMPLEMENTATION_ROADMAP.md` - Step-by-step guide
- `../TECHNICAL_ARCHITECTURE.md` - Technical specifications
