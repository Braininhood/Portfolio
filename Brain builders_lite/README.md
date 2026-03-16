# Brain Bulders

<p align="center">
  <strong>AI-Powered Mentorship Platform</strong><br>
  Connect with experts. Learn. Grow.
</p>

<p align="center">
  <a href="https://gcreators.me"><strong>Live Demo</strong></a> •
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#deployment">Deployment</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT" />
  <img src="https://img.shields.io/badge/React-18-61dafb?logo=react" alt="React 18" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Supabase-Backend-3ecf8e?logo=supabase" alt="Supabase" />
  <img src="https://img.shields.io/badge/Stripe-Payments-6772e5?logo=stripe" alt="Stripe" />
</p>

---

## Overview

**Brain Bulders** is a full-stack mentorship marketplace where experts offer consultations, digital products, and personalized guidance. Learners discover mentors through AI-powered recommendations, book sessions, purchase products, and interact via chat and AI avatars.

### Key Value Proposition

- **For Learners:** Find the right mentor, book sessions, buy digital products, and get AI-assisted support
- **For Mentors:** Monetize expertise through consultations, products, and AI avatars that scale your reach
- **For the Platform:** Stripe Connect handles payouts; Supabase powers auth, database, and realtime; AI drives discovery and engagement

---

## Features

| Feature | Description |
|---------|-------------|
| **Mentor Discovery** | Browse mentors, view profiles, and get AI-powered recommendations |
| **Consultations** | Book sessions with calendar integration (Google Calendar, Outlook) |
| **Digital Products** | Mentors sell courses, guides, and resources with instant delivery |
| **Messaging** | Direct chat between learners and mentors with real-time updates |
| **AI Avatars** | Knowledge-base-powered AI assistants for mentor products |
| **Payments** | Stripe Connect for mentor payouts and product purchases |
| **Admin Panel** | User management, sales analytics, bookings, and support tools |
| **Video Responses** | Mentors can record video answers to learner questions |
| **Translations** | Multi-language support via DeepL or Google Translate |
| **Voice AI** | Optional text-to-speech for avatar responses (ElevenLabs, Google TTS) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Radix UI |
| **Backend** | Supabase (PostgreSQL, Auth, Storage, Realtime, Edge Functions) |
| **Payments** | Stripe, Stripe Connect |
| **AI** | OpenAI / Google Gemini / Anthropic Claude |
| **Calendar** | Google Calendar API, Microsoft Graph (Outlook) |
| **Email** | Resend / SendGrid |
| **Testing** | Playwright (E2E) |

---

## Quick Start

### Prerequisites

- **Node.js** 18 or higher
- **npm** or **bun**
- **Supabase** account
- **Stripe** account (for payments)

### Installation

```bash
# Clone the repository
git clone https://github.com/Braininhood/Brain-Bulders-MVP.git
cd Brain-Bulders-MVP

# Install dependencies
npm install

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Supabase, Stripe, and other API keys

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173` (Vite default).

### Environment Variables

Copy `.env.example` to `.env` and configure the required variables. Minimum setup:

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (server-side only) |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |

See [`.env.example`](.env.example) for the full configuration reference, including AI providers, email, calendar, and optional services.

---

## Project Structure

```
Brain-Bulders-MVP/
├── src/
│   ├── components/       # React components (UI, business logic)
│   ├── pages/            # Route pages
│   ├── hooks/            # Custom React hooks
│   ├── integrations/     # Supabase client and integrations
│   └── utils/            # Helpers, validation, calendar utilities
├── supabase/
│   ├── functions/         # Edge functions (auth, webhooks, notifications)
│   │   ├── stripe-webhook/
│   │   ├── send-booking-confirmation/
│   │   ├── verify-product-purchase/
│   │   ├── chat-with-avatar/
│   │   └── ...
│   └── migrations/       # Database migrations
├── public/               # Static assets
├── scripts/              # Deployment and utility scripts
└── docs/                 # Additional documentation
```

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint |
| `npm run deploy:cancel-booking` | Deploy cancel-booking Edge Function |
| `npm run deploy:update-booking-status` | Deploy update-booking-status Edge Function |

---

## Deployment

### Frontend (Vercel / Netlify)

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Add environment variables from `.env.example`

### Supabase Edge Functions

Deploy payment-related functions:

```bash
# Windows
scripts\deploy-payment-functions.cmd

# Linux / macOS
./scripts/deploy-payment-functions.sh
```

Or deploy individual functions:

```bash
supabase functions deploy stripe-webhook --no-verify-jwt
supabase functions deploy verify-product-purchase --no-verify-jwt
```

### Stripe Webhooks

Configure your Stripe webhook endpoint to point to your deployed `stripe-webhook` function URL and subscribe to the required events.

---

## Configuration Highlights

- **AI Provider:** Choose OpenAI, Google Gemini, or Anthropic Claude via `AI_PROVIDER`
- **Translation:** DeepL or Google Translate via `TRANSLATION_PROVIDER`
- **Email:** Resend or SendGrid via `EMAIL_PROVIDER`
- **Storage:** Supabase Storage or Cloudflare R2 via `STORAGE_PROVIDER`
- **Feature Flags:** Toggle AI avatar, video responses, chat, translations via `FEATURE_*` variables

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** — see [LICENSE.md](LICENSE.md) for details.

---

<p align="center">
  <strong>Brain Bulders</strong> — Connect, learn, grow.<br>
  Founded by Vita Shafinska
</p>
