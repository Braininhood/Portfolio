-- Add reminder tracking columns to bookings table
ALTER TABLE public.bookings
ADD COLUMN IF NOT EXISTS reminder_sent_24h TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS reminder_sent_1h TIMESTAMP WITH TIME ZONE;

-- Add indexes for reminder queries
CREATE INDEX IF NOT EXISTS idx_bookings_reminder_24h ON public.bookings(booking_date, reminder_sent_24h) 
WHERE status = 'confirmed' AND reminder_sent_24h IS NULL;

CREATE INDEX IF NOT EXISTS idx_bookings_reminder_1h ON public.bookings(booking_date, reminder_sent_1h) 
WHERE status = 'confirmed' AND reminder_sent_1h IS NULL;

-- Add comment
COMMENT ON COLUMN public.bookings.reminder_sent_24h IS 'Timestamp when 24h reminder was sent';
COMMENT ON COLUMN public.bookings.reminder_sent_1h IS 'Timestamp when 1h reminder was sent';
