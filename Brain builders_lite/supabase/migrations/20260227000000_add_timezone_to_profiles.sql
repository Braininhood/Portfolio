-- Add timezone to profiles (learners and all users)
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT NULL;

COMMENT ON COLUMN public.profiles.timezone IS 'IANA timezone (e.g. Europe/Berlin, America/New_York). Used for learner and as fallback.';

-- Add timezone to mentor_profiles (mentors; used for availability and mentor dashboard)
ALTER TABLE public.mentor_profiles
  ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT NULL;

COMMENT ON COLUMN public.mentor_profiles.timezone IS 'IANA timezone for mentor. All availability and session times shown in this timezone.';

-- Update get_profiles_with_email so admin can see/edit timezone
DROP FUNCTION IF EXISTS public.get_profiles_with_email();

CREATE OR REPLACE FUNCTION public.get_profiles_with_email()
RETURNS TABLE (
  id uuid,
  full_name text,
  skill_level text,
  goals text,
  preferred_language text,
  timezone text,
  updated_at timestamptz,
  email text,
  created_at timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  ) THEN
    RAISE EXCEPTION 'Access denied. Admin role required.';
  END IF;

  RETURN QUERY
  SELECT
    p.id,
    p.full_name,
    p.skill_level,
    p.goals,
    p.preferred_language,
    p.timezone,
    p.updated_at,
    u.email::text,
    u.created_at
  FROM public.profiles p
  LEFT JOIN auth.users u ON u.id = p.id
  ORDER BY p.updated_at DESC NULLS LAST;
END;
$$;

COMMENT ON FUNCTION public.get_profiles_with_email IS
  'Returns profiles with user emails and timezone. Only accessible by admins.';
