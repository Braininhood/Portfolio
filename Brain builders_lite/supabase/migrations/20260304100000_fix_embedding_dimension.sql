-- Fix embedding column dimension: OpenAI text-embedding-3-small returns 1536 dims, not 768
-- Drop the old index first (required before altering vector column)
DROP INDEX IF EXISTS mentor_avatar_knowledge_embedding_idx;

-- Clear existing embeddings (they were generated with wrong dimension and are unusable)
UPDATE mentor_avatar_knowledge SET embedding = NULL;

-- Alter the column to the correct dimension
ALTER TABLE mentor_avatar_knowledge
  ALTER COLUMN embedding TYPE vector(1536);

-- Recreate the index with correct dimension
CREATE INDEX mentor_avatar_knowledge_embedding_idx
  ON mentor_avatar_knowledge
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Fix the match_avatar_knowledge RPC to use correct dimension
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
