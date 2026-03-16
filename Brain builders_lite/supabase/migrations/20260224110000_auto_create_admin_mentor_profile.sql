-- Auto-create a mentor_profile for users when they get the admin role, so "Message admin" works for learners.
-- Runs with SECURITY DEFINER so it can insert despite RLS.

CREATE OR REPLACE FUNCTION public.ensure_admin_mentor_profile()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  admin_user_id UUID := NEW.user_id;
  admin_name TEXT;
BEGIN
  IF NEW.role <> 'admin' THEN
    RETURN NEW;
  END IF;

  IF EXISTS (SELECT 1 FROM public.mentor_profiles WHERE user_id = admin_user_id) THEN
    RETURN NEW;
  END IF;

  SELECT COALESCE(p.full_name, 'Admin') INTO admin_name
  FROM public.profiles p
  WHERE p.id = admin_user_id
  LIMIT 1;

  IF admin_name IS NULL THEN
    admin_name := 'Admin';
  END IF;

  INSERT INTO public.mentor_profiles (
    user_id,
    name,
    title,
    category,
    bio,
    full_bio,
    expertise,
    languages,
    availability,
    experience,
    education,
    certifications,
    price,
    is_active
  ) VALUES (
    admin_user_id,
    admin_name,
    'Administrator',
    'Business',
    'Platform administrator',
    'Platform administrator',
    ARRAY['Administration'],
    ARRAY['English'],
    'Available',
    'Platform administration',
    'N/A',
    ARRAY[]::TEXT[],
    0,
    false
  );

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ensure_admin_mentor_profile_trigger ON public.user_roles;
CREATE TRIGGER ensure_admin_mentor_profile_trigger
  AFTER INSERT ON public.user_roles
  FOR EACH ROW
  EXECUTE FUNCTION public.ensure_admin_mentor_profile();

-- Backfill: create mentor_profile for every existing admin who doesn't have one
INSERT INTO public.mentor_profiles (
  user_id,
  name,
  title,
  category,
  bio,
  full_bio,
  expertise,
  languages,
  availability,
  experience,
  education,
  certifications,
  price,
  is_active
)
SELECT
  ur.user_id,
  COALESCE(p.full_name, 'Admin'),
  'Administrator',
  'Business',
  'Platform administrator',
  'Platform administrator',
  ARRAY['Administration'],
  ARRAY['English'],
  'Available',
  'Platform administration',
  'N/A',
  ARRAY[]::TEXT[],
  0,
  false
FROM public.user_roles ur
LEFT JOIN public.profiles p ON p.id = ur.user_id
WHERE ur.role = 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM public.mentor_profiles mp WHERE mp.user_id = ur.user_id
  );
