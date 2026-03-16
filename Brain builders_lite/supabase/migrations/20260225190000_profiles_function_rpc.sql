-- Replace the view with a SECURITY DEFINER function that admins can call
-- This bypasses RLS and allows admins to see user emails

-- Drop the view
DROP VIEW IF EXISTS public.profiles_with_email;

-- Create a function that returns profiles with emails (only for admins)
CREATE OR REPLACE FUNCTION public.get_profiles_with_email()
RETURNS TABLE (
  id uuid,
  full_name text,
  skill_level text,
  goals text,
  preferred_language text,
  updated_at timestamptz,
  email text,
  created_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Check if user is admin
  IF NOT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  ) THEN
    RAISE EXCEPTION 'Access denied. Admin role required.';
  END IF;

  -- Return profiles with emails
  RETURN QUERY
  SELECT 
    p.id,
    p.full_name,
    p.skill_level,
    p.goals,
    p.preferred_language,
    p.updated_at,
    u.email::text,
    u.created_at
  FROM public.profiles p
  LEFT JOIN auth.users u ON u.id = p.id
  ORDER BY p.updated_at DESC NULLS LAST;
END;
$$;

COMMENT ON FUNCTION public.get_profiles_with_email IS 
  'Returns profiles with user emails. Only accessible by admins. Use via RPC call.';
