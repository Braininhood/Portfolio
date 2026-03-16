# MultiBook - Next.js Frontend

## Overview

This is the Next.js 14+ frontend for the MultiBook multi-service booking system. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Project Structure

```
frontend/
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
│   │   ├── staff/
│   │   ├── customers/
│   │   └── reports/
│   ├── ad/                 # Admin routes (Security: /ad/)
│   │   ├── dashboard/
│   │   ├── calendar/
│   │   ├── appointments/
│   │   ├── staff/
│   │   ├── customers/
│   │   ├── managers/
│   │   └── settings/
│   ├── booking/           # Public booking flow (guest checkout)
│   │   ├── postcode/      # Step 1: Postcode entry
│   │   ├── services/      # Step 2: Service selection
│   │   ├── date-time/     # Step 3: Date & time
│   │   ├── booking-type/  # Step 4: Booking type (Single/Subscription/Order)
│   │   ├── details/       # Step 5: Guest details & payment
│   │   └── confirmation/  # Step 6: Confirmation + account linking
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
│
├── components/            # React components
│   ├── ui/                # shadcn/ui components
│   ├── booking/           # Booking-specific components
│   ├── calendar/          # Calendar components
│   └── forms/             # Form components
│
├── lib/                   # Utilities
│   ├── api/               # API client (axios)
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   └── constants/         # Constants
│
├── types/                 # TypeScript type definitions
│   ├── api.ts             # API response types
│   ├── models.ts          # Data model types
│   └── auth.ts            # Authentication types
│
├── store/                 # State management (Zustand)
│   ├── auth-store.ts      # Authentication state
│   ├── booking-store.ts   # Booking flow state
│   └── user-store.ts      # User state
│
├── hooks/                 # Custom React hooks
│   ├── use-auth.ts        # Authentication hook
│   ├── use-api.ts         # API call hook
│   └── use-booking.ts     # Booking flow hook
│
├── styles/                # Global styles
│   └── globals.css        # Tailwind CSS imports
│
├── public/                # Static files
│   ├── images/
│   └── icons/
│
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
└── .env.local.example
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
copy .env.local.example .env.local  # Windows
# or
cp .env.local.example .env.local    # Linux/Mac
```

Update `.env.local` with your API URL:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Key Features

- ✅ **Security Prefixes** - All routes use shortened prefixes (/cus/, /st/, /man/, /ad/)
- ✅ **Guest Checkout** - Booking flow without login/registration
- ✅ **Postcode-First Booking** - Start with postcode entry
- ✅ **TypeScript** - Full type safety
- ✅ **Tailwind CSS** - Utility-first styling
- ✅ **shadcn/ui** - Accessible component library
- ✅ **Zustand** - State management
- ✅ **React Query** - Data fetching and caching
- ✅ **React Hook Form** - Form management with Zod validation

## API Integration

The frontend uses axios for API calls to the Django backend at `http://localhost:8000/api`.

All API endpoints use security prefixes:
- Public: `/api/v1/svc/`, `/api/v1/stf/`, `/api/v1/bkg/`, etc.
- Protected: `/api/v1/cus/`, `/api/v1/st/`, `/api/v1/man/`, `/api/v1/ad/`

## Next Steps

After setup, follow the IMPLEMENTATION_ROADMAP.md for:
- Week 1 Day 5: Database Models (backend)
- Week 2: Authentication System (frontend + backend)
- Week 3: Basic Booking Flow (frontend + backend)
- And so on...

## Documentation

See the main project documentation:
- `../MULTIBOOK_BEST_SOLUTION.md` - Complete solution
- `../IMPLEMENTATION_ROADMAP.md` - Step-by-step guide
- `../TECHNICAL_ARCHITECTURE.md` - Technical specifications
