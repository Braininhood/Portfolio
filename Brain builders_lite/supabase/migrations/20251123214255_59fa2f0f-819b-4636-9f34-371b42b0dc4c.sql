-- Add pinned column to messages table
ALTER TABLE public.messages
ADD COLUMN pinned boolean NOT NULL DEFAULT false;