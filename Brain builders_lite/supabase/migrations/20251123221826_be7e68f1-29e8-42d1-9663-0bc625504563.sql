-- Create message_reminders table
CREATE TABLE IF NOT EXISTS public.message_reminders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL,
  user_id UUID NOT NULL,
  conversation_id UUID NOT NULL,
  reminder_time TIMESTAMP WITH TIME ZONE NOT NULL,
  note TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  sent_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS
ALTER TABLE public.message_reminders ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can create reminders in their conversations"
  ON public.message_reminders
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM public.conversations
      WHERE id = message_reminders.conversation_id
      AND user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view their own reminders"
  ON public.message_reminders
  FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can update their own reminders"
  ON public.message_reminders
  FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own reminders"
  ON public.message_reminders
  FOR DELETE
  USING (user_id = auth.uid());

-- Indexes
CREATE INDEX idx_message_reminders_user_id ON public.message_reminders(user_id);
CREATE INDEX idx_message_reminders_message_id ON public.message_reminders(message_id);
CREATE INDEX idx_message_reminders_reminder_time ON public.message_reminders(reminder_time) WHERE status = 'pending';

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.message_reminders;