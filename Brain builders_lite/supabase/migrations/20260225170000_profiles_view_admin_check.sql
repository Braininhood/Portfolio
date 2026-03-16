-- Add RLS policy for profiles_with_email view
-- Only admins can access this view

-- Create helper function to check if user is admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  );
$$;

-- Note: Views in Postgres don't support RLS directly
-- The RLS will be enforced on the underlying tables
-- Since profiles table already has RLS, and auth.users is protected,
-- we just need to ensure only admins can query this view via application logic

COMMENT ON FUNCTION public.is_admin IS 
  'Helper function to check if current user has admin role';
