-- Create message_read_receipts table
CREATE TABLE public.message_read_receipts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  read_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(message_id, user_id)
);

-- Enable Row Level Security
ALTER TABLE public.message_read_receipts ENABLE ROW LEVEL SECURITY;

-- Create policies for message_read_receipts
CREATE POLICY "Users can view read receipts in their conversations"
  ON public.message_read_receipts
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.conversations
      WHERE conversations.id = message_read_receipts.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create read receipts in their conversations"
  ON public.message_read_receipts
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM public.conversations
      WHERE conversations.id = message_read_receipts.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );

-- Create index for faster lookups
CREATE INDEX idx_message_read_receipts_message ON public.message_read_receipts(message_id);
CREATE INDEX idx_message_read_receipts_conversation ON public.message_read_receipts(conversation_id);

-- Enable realtime for read receipts
ALTER PUBLICATION supabase_realtime ADD TABLE public.message_read_receipts;