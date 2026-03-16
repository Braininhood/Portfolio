-- Add soft delete system for conversations
-- Users can "delete" conversations from their view without affecting others

-- Track which users have hidden/deleted a conversation
CREATE TABLE IF NOT EXISTS public.conversation_deletions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  deleted_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(conversation_id, user_id)
);

COMMENT ON TABLE public.conversation_deletions IS 
  'Tracks which users have deleted/hidden a conversation from their view. Conversations are never actually deleted, just hidden per-user.';

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_conversation_deletions_user 
  ON public.conversation_deletions(user_id);

CREATE INDEX IF NOT EXISTS idx_conversation_deletions_conversation 
  ON public.conversation_deletions(conversation_id);

-- RLS policies
ALTER TABLE public.conversation_deletions ENABLE ROW LEVEL SECURITY;

-- Users can see their own deletions
CREATE POLICY "Users can view own deletions"
  ON public.conversation_deletions
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can delete conversations (add to deletions table)
CREATE POLICY "Users can mark conversations as deleted"
  ON public.conversation_deletions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can restore conversations (remove from deletions table)
CREATE POLICY "Users can restore conversations"
  ON public.conversation_deletions
  FOR DELETE
  USING (auth.uid() = user_id);
