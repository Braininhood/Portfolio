-- Add last_seen_at to profiles for "Online" status in admin (within last 5 min = online)
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS last_seen_at timestamptz DEFAULT now();

COMMENT ON COLUMN public.profiles.last_seen_at IS 'Updated by client on activity; admin shows Online if within last few minutes.';
