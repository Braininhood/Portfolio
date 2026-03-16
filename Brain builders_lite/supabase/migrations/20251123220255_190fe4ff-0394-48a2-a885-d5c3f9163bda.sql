-- Add read_at timestamp column to messages table
ALTER TABLE public.messages
ADD COLUMN read_at TIMESTAMP WITH TIME ZONE;

-- Update existing read messages to have a read_at timestamp (set to created_at as fallback)
UPDATE public.messages
SET read_at = created_at
WHERE is_read = true AND read_at IS NULL;