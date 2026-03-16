-- Add claiming system for support conversations
-- When first admin responds, conversation is "claimed" and only that admin sees it

ALTER TABLE public.conversations
  ADD COLUMN IF NOT EXISTS claimed_by_admin_id uuid REFERENCES auth.users(id);

COMMENT ON COLUMN public.conversations.claimed_by_admin_id IS 
  'When an admin first responds to a support conversation, this is set to their user_id. Only that admin will see the conversation afterwards.';

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_claimed_by_admin 
  ON public.conversations(claimed_by_admin_id);
