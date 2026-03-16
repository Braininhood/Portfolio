-- Create scheduled messages table
CREATE TABLE public.scheduled_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  sender_id uuid NOT NULL,
  sender_name text NOT NULL,
  content text NOT NULL,
  file_url text,
  file_name text,
  file_type text,
  scheduled_for timestamp with time zone NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  sent_at timestamp with time zone,
  error_message text,
  CONSTRAINT valid_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled'))
);

-- Create index for efficient querying
CREATE INDEX idx_scheduled_messages_pending ON public.scheduled_messages(scheduled_for) 
WHERE status = 'pending';

-- Enable RLS
ALTER TABLE public.scheduled_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own scheduled messages"
  ON public.scheduled_messages
  FOR SELECT
  USING (
    sender_id = auth.uid() OR
    EXISTS (
      SELECT 1 FROM public.conversations
      WHERE conversations.id = scheduled_messages.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create scheduled messages in their conversations"
  ON public.scheduled_messages
  FOR INSERT
  WITH CHECK (
    sender_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM public.conversations
      WHERE conversations.id = scheduled_messages.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update their own scheduled messages"
  ON public.scheduled_messages
  FOR UPDATE
  USING (sender_id = auth.uid());

CREATE POLICY "Users can delete their own scheduled messages"
  ON public.scheduled_messages
  FOR DELETE
  USING (sender_id = auth.uid());