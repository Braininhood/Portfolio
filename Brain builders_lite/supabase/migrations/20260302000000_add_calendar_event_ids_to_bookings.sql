-- Add calendar event ID columns to bookings table
ALTER TABLE public.bookings
ADD COLUMN IF NOT EXISTS mentor_calendar_event_id TEXT,
ADD COLUMN IF NOT EXISTS learner_calendar_event_id TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_bookings_mentor_calendar_event ON public.bookings(mentor_calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_bookings_learner_calendar_event ON public.bookings(learner_calendar_event_id);

-- Add comment
COMMENT ON COLUMN public.bookings.mentor_calendar_event_id IS 'Google Calendar event ID for mentor';
COMMENT ON COLUMN public.bookings.learner_calendar_event_id IS 'Google Calendar event ID for learner';
