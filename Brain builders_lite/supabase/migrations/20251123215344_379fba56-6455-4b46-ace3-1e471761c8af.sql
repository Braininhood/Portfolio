-- Add reply_to column to messages table
ALTER TABLE public.messages
ADD COLUMN reply_to uuid REFERENCES public.messages(id) ON DELETE SET NULL;

-- Create index for efficient thread queries
CREATE INDEX idx_messages_reply_to ON public.messages(reply_to)
WHERE reply_to IS NOT NULL;