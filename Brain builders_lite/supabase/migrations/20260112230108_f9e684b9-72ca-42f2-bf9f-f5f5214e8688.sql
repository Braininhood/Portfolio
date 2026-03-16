-- Create mentor_weekly_availability table for recurring weekly schedules
CREATE TABLE IF NOT EXISTS public.mentor_weekly_availability (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_mentor_weekly_availability_mentor_id ON public.mentor_weekly_availability(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_weekly_availability_day ON public.mentor_weekly_availability(day_of_week);

-- Enable RLS
ALTER TABLE public.mentor_weekly_availability ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Mentors can manage their own availability
CREATE POLICY "Mentors can manage their own weekly availability"
ON public.mentor_weekly_availability
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_weekly_availability.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_weekly_availability.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- Public can view active availability
CREATE POLICY "Anyone can view active weekly availability"
ON public.mentor_weekly_availability
FOR SELECT
USING (is_active = true);

-- Create mentor_calendar_connections table for Google Calendar sync
CREATE TABLE IF NOT EXISTS public.mentor_calendar_connections (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'google',
  access_token TEXT,
  refresh_token TEXT,
  token_expires_at TIMESTAMP WITH TIME ZONE,
  calendar_id TEXT,
  sync_enabled BOOLEAN NOT NULL DEFAULT false,
  last_synced_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(mentor_id, provider)
);

-- Enable RLS
ALTER TABLE public.mentor_calendar_connections ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Mentors can manage their own calendar connections
CREATE POLICY "Mentors can manage their own calendar connections"
ON public.mentor_calendar_connections
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_calendar_connections.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_calendar_connections.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
);