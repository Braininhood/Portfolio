-- Add edited_at column to messages table
ALTER TABLE public.messages
ADD COLUMN edited_at timestamp with time zone;