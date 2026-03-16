-- Create message_reactions table
CREATE TABLE public.message_reactions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  message_id UUID NOT NULL,
  user_id UUID NOT NULL,
  emoji TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(message_id, user_id, emoji)
);

-- Enable RLS
ALTER TABLE public.message_reactions ENABLE ROW LEVEL SECURITY;

-- Users can view reactions in their conversations
CREATE POLICY "Users can view reactions in their conversations"
ON public.message_reactions FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM messages
    JOIN conversations ON conversations.id = messages.conversation_id
    WHERE messages.id = message_reactions.message_id
    AND conversations.user_id = auth.uid()
  )
);

-- Users can add reactions to messages in their conversations
CREATE POLICY "Users can add reactions"
ON public.message_reactions FOR INSERT
WITH CHECK (
  auth.uid() = user_id AND
  EXISTS (
    SELECT 1 FROM messages
    JOIN conversations ON conversations.id = messages.conversation_id
    WHERE messages.id = message_reactions.message_id
    AND conversations.user_id = auth.uid()
  )
);

-- Users can delete their own reactions
CREATE POLICY "Users can delete their own reactions"
ON public.message_reactions FOR DELETE
USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX idx_message_reactions_message_id ON public.message_reactions(message_id);