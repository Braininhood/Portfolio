-- Create archived_users table to store deleted user data
CREATE TABLE IF NOT EXISTS public.archived_users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  original_user_id uuid NOT NULL,
  user_data jsonb NOT NULL,
  profiles_data jsonb,
  mentor_profiles_data jsonb,
  user_roles_data jsonb,
  conversations_data jsonb,
  messages_data jsonb,
  bookings_data jsonb,
  products_data jsonb,
  avatars_data jsonb,
  deleted_at timestamptz NOT NULL DEFAULT now(),
  deleted_by uuid REFERENCES auth.users(id),
  deletion_reason text,
  
  CONSTRAINT archived_users_original_user_id_key UNIQUE(original_user_id, deleted_at)
);

COMMENT ON TABLE public.archived_users IS 
  'Archive of deleted users with all their data preserved in JSON format';

-- Index for faster searches
CREATE INDEX IF NOT EXISTS idx_archived_users_original_id 
  ON public.archived_users(original_user_id);

CREATE INDEX IF NOT EXISTS idx_archived_users_deleted_at 
  ON public.archived_users(deleted_at DESC);

-- RLS policies for archived_users
ALTER TABLE public.archived_users ENABLE ROW LEVEL SECURITY;

-- Only admins can view archived users
CREATE POLICY "Admins can view archived users"
  ON public.archived_users
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- Only admins can archive users
CREATE POLICY "Admins can archive users"
  ON public.archived_users
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );
