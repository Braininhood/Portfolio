-- Add delivered_at timestamp column to messages table
ALTER TABLE public.messages
ADD COLUMN delivered_at TIMESTAMP WITH TIME ZONE;

-- Update existing messages to have a delivered_at timestamp (set to created_at as fallback for old messages)
UPDATE public.messages
SET delivered_at = created_at
WHERE delivered_at IS NULL;