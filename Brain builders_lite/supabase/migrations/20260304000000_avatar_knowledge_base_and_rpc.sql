-- Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- match_avatar_knowledge RPC (used by chat-with-avatar)
-- ============================================================
CREATE OR REPLACE FUNCTION match_avatar_knowledge(
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  avatar_id_param uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  content_type text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    mak.id,
    mak.content,
    mak.content_type,
    mak.metadata,
    1 - (mak.embedding <=> query_embedding) AS similarity
  FROM mentor_avatar_knowledge mak
  WHERE
    mak.avatar_id = avatar_id_param
    AND mak.embedding IS NOT NULL
    AND 1 - (mak.embedding <=> query_embedding) > match_threshold
  ORDER BY mak.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================================
-- mentor_knowledge_base: mentor-uploaded custom content
-- ============================================================
CREATE TABLE IF NOT EXISTS mentor_knowledge_base (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mentor_id uuid NOT NULL REFERENCES mentor_profiles(id) ON DELETE CASCADE,
  avatar_id uuid REFERENCES mentor_avatars(id) ON DELETE SET NULL,
  title text NOT NULL,
  content text NOT NULL,
  content_type text NOT NULL DEFAULT 'text',
  -- content_type: 'text' | 'faq' | 'service' | 'bio' | 'product'
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE mentor_knowledge_base ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Mentors can manage their own knowledge base"
  ON mentor_knowledge_base
  FOR ALL
  USING (
    mentor_id IN (
      SELECT id FROM mentor_profiles WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Anyone can read active knowledge base entries"
  ON mentor_knowledge_base
  FOR SELECT
  USING (is_active = true);

CREATE INDEX IF NOT EXISTS mentor_knowledge_base_mentor_id_idx
  ON mentor_knowledge_base(mentor_id);

CREATE INDEX IF NOT EXISTS mentor_knowledge_base_avatar_id_idx
  ON mentor_knowledge_base(avatar_id);

-- ============================================================
-- avatar_usage_stats: track token/message usage per avatar
-- ============================================================
CREATE TABLE IF NOT EXISTS avatar_usage_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  avatar_id uuid NOT NULL REFERENCES mentor_avatars(id) ON DELETE CASCADE,
  conversation_id uuid REFERENCES avatar_conversations(id) ON DELETE SET NULL,
  user_id uuid REFERENCES profiles(id) ON DELETE SET NULL,
  tokens_used integer NOT NULL DEFAULT 0,
  messages_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE avatar_usage_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Mentors can view their avatar usage"
  ON avatar_usage_stats
  FOR SELECT
  USING (
    avatar_id IN (
      SELECT ma.id FROM mentor_avatars ma
      JOIN mentor_profiles mp ON mp.id = ma.mentor_id
      WHERE mp.user_id = auth.uid()
    )
  );

CREATE POLICY "System can insert usage stats"
  ON avatar_usage_stats
  FOR INSERT
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS avatar_usage_stats_avatar_id_idx
  ON avatar_usage_stats(avatar_id);

-- ============================================================
-- Helper view: avatar analytics summary per avatar
-- ============================================================
CREATE OR REPLACE VIEW avatar_analytics AS
SELECT
  ma.id AS avatar_id,
  ma.mentor_id,
  COUNT(DISTINCT ac.id) AS total_conversations,
  COUNT(DISTINCT am.id) AS total_messages,
  COALESCE(SUM(aus.tokens_used), 0) AS total_tokens_used,
  COUNT(DISTINCT ac.user_id) AS unique_users,
  MAX(ac.created_at) AS last_conversation_at
FROM mentor_avatars ma
LEFT JOIN avatar_conversations ac ON ac.avatar_id = ma.id
LEFT JOIN avatar_messages am ON am.conversation_id = ac.id AND am.role = 'user'
LEFT JOIN avatar_usage_stats aus ON aus.avatar_id = ma.id
GROUP BY ma.id, ma.mentor_id;
