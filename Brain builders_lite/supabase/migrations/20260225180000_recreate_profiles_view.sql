-- Recreate profiles_with_email view if it doesn't exist
-- This view is essential for the admin panel to access user emails

DROP VIEW IF EXISTS public.profiles_with_email;

CREATE VIEW public.profiles_with_email AS
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

-- Add comment
COMMENT ON VIEW public.profiles_with_email IS 
  'View that combines profiles with email from auth.users. Used by admin panel.';
