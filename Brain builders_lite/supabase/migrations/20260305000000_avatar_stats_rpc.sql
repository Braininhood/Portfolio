-- RPC: get stats for a single mentor's avatar (used by mentor dashboard)
CREATE OR REPLACE FUNCTION get_avatar_stats(p_avatar_id uuid)
RETURNS TABLE (
  total_conversations bigint,
  total_user_messages bigint,
  unique_users bigint,
  total_tokens_used bigint,
  last_conversation_at timestamptz
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    COUNT(DISTINCT ac.id)                                         AS total_conversations,
    COUNT(DISTINCT am.id) FILTER (WHERE am.role = 'user')        AS total_user_messages,
    COUNT(DISTINCT ac.user_id)                                    AS unique_users,
    COALESCE(SUM((am.metadata->>'tokens_used')::int)
      FILTER (WHERE am.metadata->>'tokens_used' IS NOT NULL), 0) AS total_tokens_used,
    MAX(ac.created_at)                                            AS last_conversation_at
  FROM avatar_conversations ac
  LEFT JOIN avatar_messages am ON am.conversation_id = ac.id
  WHERE ac.avatar_id = p_avatar_id;
$$;

-- RPC: get all avatar stats for admin monitoring
CREATE OR REPLACE FUNCTION get_all_avatar_stats()
RETURNS TABLE (
  avatar_id uuid,
  avatar_name text,
  mentor_name text,
  mentor_id uuid,
  status text,
  total_conversations bigint,
  total_user_messages bigint,
  unique_users bigint,
  total_tokens_used bigint,
  last_conversation_at timestamptz,
  last_trained_at timestamptz
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    ma.id                                                         AS avatar_id,
    ma.avatar_name,
    mp.name                                                       AS mentor_name,
    mp.id                                                         AS mentor_id,
    ma.status,
    COUNT(DISTINCT ac.id)                                         AS total_conversations,
    COUNT(DISTINCT am.id) FILTER (WHERE am.role = 'user')        AS total_user_messages,
    COUNT(DISTINCT ac.user_id)                                    AS unique_users,
    COALESCE(SUM((am.metadata->>'tokens_used')::int)
      FILTER (WHERE am.metadata->>'tokens_used' IS NOT NULL), 0) AS total_tokens_used,
    MAX(ac.created_at)                                            AS last_conversation_at,
    ma.last_trained_at
  FROM mentor_avatars ma
  JOIN mentor_profiles mp ON mp.id = ma.mentor_id
  LEFT JOIN avatar_conversations ac ON ac.avatar_id = ma.id
  LEFT JOIN avatar_messages am ON am.conversation_id = ac.id
  GROUP BY ma.id, ma.avatar_name, mp.name, mp.id, ma.status, ma.last_trained_at
  ORDER BY total_conversations DESC;
$$;

-- RPC: check how many messages a user has sent to an avatar (for limits)
CREATE OR REPLACE FUNCTION get_user_message_count(p_avatar_id uuid, p_user_id uuid)
RETURNS integer
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT COUNT(am.id)::integer
  FROM avatar_messages am
  JOIN avatar_conversations ac ON ac.id = am.conversation_id
  WHERE ac.avatar_id = p_avatar_id
    AND ac.user_id = p_user_id
    AND am.role = 'user';
$$;
