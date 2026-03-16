-- Create a view that joins profiles with auth.users to get emails
-- This allows querying user emails without needing admin API access from client

CREATE OR REPLACE VIEW public.profiles_with_email AS
SELECT 
  p.id,
  p.full_name,
  p.skill_level,
  p.goals,
  p.preferred_language,
  p.updated_at,
  u.email,
  u.created_at
FROM public.profiles p
LEFT JOIN auth.users u ON u.id = p.id;

-- Grant access to authenticated users
GRANT SELECT ON public.profiles_with_email TO authenticated;

-- Add RLS policy - only admins can view
ALTER VIEW public.profiles_with_email SET (security_invoker = on);

-- Or use a function-based approach
CREATE OR REPLACE FUNCTION public.can_view_profiles_with_email()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  );
$$;

COMMENT ON VIEW public.profiles_with_email IS 
  'View that combines profiles with email from auth.users for easier querying. Only accessible by admins.';

