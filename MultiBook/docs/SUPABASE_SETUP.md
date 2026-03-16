# Supabase Setup (MultiBook)

This project uses **Supabase** for:

- **Database**: PostgreSQL hosted on Supabase (Django connects via `DATABASE_URL`).
- **Auth (optional)**: Supabase Auth for sign-in/sign-up and Google OAuth (frontend uses `@/lib/supabase/client` and `useSupabaseAuth`).
- **Storage (optional)**: Backend can use `apps.core.supabase_storage` for file uploads.

---

## Backend (Django)

- **Database**: Set `DATABASE_URL` in `backend/.env` to your Supabase Postgres connection string:
  - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`
  - If the password contains `@` or `#`, URL-encode it (e.g. `@` → `%40`).
- **Supabase API**: In `backend/.env` set:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- **Settings**: `config.settings.development` parses `DATABASE_URL` and URL-decodes the password; Supabase vars are read in `config.settings.base`.
- **Migrations**: Schema is created in Supabase by running:
  ```powershell
  cd backend
  .\venv\Scripts\python.exe manage.py migrate --settings=config.settings.development
  ```
- **Secrets**: Never commit `backend/.env`. Use `backend/.env.example` as a template (placeholders only).

---

## Frontend (Next.js)

- **Supabase client**: Uses `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `frontend/.env.local` (see `frontend/.env.example`).
- **Google OAuth**: Enable in [Supabase Dashboard](https://supabase.com/dashboard) → your project → **Authentication** → **Providers** → **Google**, then add your Google OAuth client ID/secret.
- **Fix "Error 400: redirect_uri_mismatch"**: Google must allow Supabase’s callback URL. In [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials** → open your **OAuth 2.0 Client ID** (Web application) → **Authorized redirect URIs** → add:
  - **`https://[YOUR_PROJECT_REF].supabase.co/auth/v1/callback`**
  - Replace `[YOUR_PROJECT_REF]` with your Supabase project reference (from your Supabase Dashboard). Find it in Supabase Dashboard → **Settings** → **API** (Project URL contains it). Save the client; try “Sign in with Google” again.
- **Usage**: `lib/supabase/client.ts` creates the Supabase client; `hooks/use-supabase-auth.ts` provides `signIn`, `signUp`, `signOut`, etc. Use these for Supabase Auth (including Google OAuth).
- **Secrets**: Never put the service role key on the frontend. Only anon/publishable key is safe in `NEXT_PUBLIC_*`.

---

## Database in Supabase

The **correct DB** is the default `postgres` database on your Supabase project. Django migrations create all app tables there (e.g. `accounts_user`, `services_service`, `orders_order`, `appointments_appointment`, etc.). You do not create a separate "MultiBook database"; use the same project and run migrations as above.

**Create all tables from SQL (all role types: customer, staff, manager, admin):** Run `python manage.py export_schema_sql -o supabase_schema.sql --settings=config.settings.development` in `backend`, then run `backend/supabase_schema.sql` in Supabase SQL Editor. Then run `backend/supabase_enable_rls.sql` for RLS.

### Seed simple data (same as used for local DB)

After migrations (or after creating tables from SQL), load sample data: admin/customer/staff/manager users, categories, services, staff, schedules, areas, sample appointments.

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_data --settings=config.settings.development
```

- **Admin:** `admin@multibook.local` (default password: `ChangeMe123!`) — Django admin.
- **Customer:** `customer@multibook.test` (default password: `ChangeMe123!`) — customer portal.
- **Staff portal:** first staff e.g. `john.smith@multibook.test` (default password: `ChangeMe123!`).
- **Manager:** `manager@multibook.local` (default password: `ChangeMe123!`).

Override passwords with env: `SEED_ADMIN_PASSWORD`, `SEED_CUSTOMER_PASSWORD`, `SEED_STAFF_PASSWORD`, `SEED_MANAGER_PASSWORD`. Use `--no-sample` to only create users (no categories/services/staff/appointments).

**Seed Feb 2026 appointments (for date-time slot testing):**  
`python manage.py seed_feb_appointments --settings=config.settings.development`  
Adds random appointments across staff for 1–28 Feb 2026. Use `--clear` to remove existing Feb 2026 appointments first.

---

## Row Level Security (RLS) – fix "exposed via API without RLS"

Supabase warns when tables (e.g. `public.django_session`) are exposed via the Supabase REST API without RLS and contain sensitive columns. Django uses the **postgres** connection (bypasses RLS); the Supabase API uses anon/authenticated roles. Enabling RLS on all `public` tables blocks API access to those tables while keeping Django access.

1. In **Supabase Dashboard** → **SQL Editor**, create a new query.
2. Paste and run the contents of **`backend/supabase_enable_rls.sql`**.
3. This enables RLS on every table in `public`. With no permissive policies, the Supabase REST API can no longer read or write those tables; Django (postgres user) is unaffected.

---

## Migrate data from local DB to Supabase

**Source options:** local **PostgreSQL** (if your data is in Postgres) or local **SQLite** (`backend/db.sqlite3`).

**Option A – From local PostgreSQL:** Set `LOCAL_DATABASE_URL=postgresql://user:password@localhost:5432/multibook_local` in `backend/.env`. Keep `DATABASE_URL` pointing at Supabase. Run `.\migrate_local_to_supabase.ps1` from `backend`.

**Option B – From local SQLite:** Put your local DB at `backend/db.sqlite3` (same Django schema; if you see "no such table", the script will run migrate on SQLite first). Ensure `DATABASE_URL` points to Supabase. Run `.\migrate_local_to_supabase.ps1` from `backend`.

The backup file `data_backup.json` is kept (gitignored); you can delete it after verifying.

---

## Checklist

- [x] `backend/.env` has `DATABASE_URL` (Supabase Postgres) and Supabase API vars.
- [x] `backend/.env.example` has placeholders only (no real secrets).
- [x] `frontend/.env.local` has `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [x] `.gitignore` excludes `.env` and `.env.local` (backend, frontend, and repo root).
- [x] Migrations have been run so the schema exists in Supabase.
- [ ] Google OAuth enabled in Supabase Dashboard if you use “Sign in with Google”.
