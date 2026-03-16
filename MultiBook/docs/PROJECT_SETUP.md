# MultiBook Booking System - Project Setup Guide

## Overview

This document provides step-by-step instructions for setting up the MultiBook booking system project structure based on the solution documents.

## Project Structure

```
MultiBook/
├── backend/              # Django Backend (localhost:8000)
│   ├── config/          # Django settings
│   ├── apps/            # Django apps
│   ├── requirements.txt # Python dependencies
│   └── manage.py
│
├── frontend/            # Next.js Frontend (localhost:3000)
│   ├── app/            # Next.js App Router
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   └── package.json
│
└── docs/               # Documentation (already created)
    ├── MULTIBOOK_BEST_SOLUTION.md
    ├── IMPLEMENTATION_ROADMAP.md
    ├── TECHNICAL_ARCHITECTURE.md
    └── ...
```

## Step-by-Step Setup

### Step 1: Backend Setup (Django)

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize Django project:**
   ```bash
   django-admin startproject config .
   ```

6. **Create Django apps structure:**
   ```bash
   python manage.py startapp core
   python manage.py startapp accounts
   python manage.py startapp services
   python manage.py startapp staff
   python manage.py startapp customers
   python manage.py startapp appointments
   python manage.py startapp payments
   python manage.py startapp subscriptions
   python manage.py startapp orders
   python manage.py startapp notifications
   python manage.py startapp calendar_sync
   ```

7. **Copy environment file:**
   ```bash
   copy env.example .env  # Windows
   # or
   cp env.example .env    # Linux/Mac
   ```

8. **Generate SECRET_KEY:**
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```
   Update `.env` file with the generated SECRET_KEY.

9. **Run initial migrations:**
   ```bash
   python manage.py migrate
   ```

10. **Create superuser:**
    ```bash
    python manage.py createsuperuser
    ```

11. **Run development server:**
    ```bash
    python manage.py runserver
    ```
    Backend should be available at `http://localhost:8000`

### Step 2: Frontend Setup (Next.js)

1. **Navigate to project root:**
   ```bash
   cd ..
   ```

2. **Create Next.js project:**
   ```bash
   npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir
   ```

3. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

4. **Install additional dependencies:**
   ```bash
   npm install axios zustand react-hook-form zod @tanstack/react-query
   npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
   npm install date-fns fullcalendar
   ```

5. **Install shadcn/ui:**
   ```bash
   npx shadcn-ui@latest init
   ```

6. **Create environment file:**
   Create `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

7. **Run development server:**
   ```bash
   npm run dev
   ```
   Frontend should be available at `http://localhost:3000`

## Next Steps

After setup, follow the IMPLEMENTATION_ROADMAP.md for:
- Week 1 Day 5: Database Models
- Week 2: Authentication & Core API
- Week 3: Basic Booking Flow
- And so on...

## Important Notes

- **Development Database:** SQLite (db.sqlite3) - already configured
- **API Endpoints:** Use shortened security prefixes (/api/cus/, /api/st/, /api/man/, /api/ad/)
- **Guest Checkout:** No login required for booking
- **Security:** All endpoints use shortened prefixes for security

## Documentation References

- **MULTIBOOK_BEST_SOLUTION.md** - Complete solution details
- **IMPLEMENTATION_ROADMAP.md** - Step-by-step implementation guide
- **TECHNICAL_ARCHITECTURE.md** - Technical specifications
- **README.md** - Project overview
