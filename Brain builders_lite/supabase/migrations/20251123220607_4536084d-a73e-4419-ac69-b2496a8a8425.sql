-- Add archived column to conversations table
ALTER TABLE public.conversations
ADD COLUMN archived BOOLEAN NOT NULL DEFAULT false;

-- Add archived_at timestamp column
ALTER TABLE public.conversations
ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;

-- Create index for faster queries on archived conversations
CREATE INDEX idx_conversations_archived ON public.conversations(user_id, archived);