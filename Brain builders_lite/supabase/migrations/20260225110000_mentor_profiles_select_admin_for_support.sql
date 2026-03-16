-- Allow anyone to view mentor_profiles that belong to admin users, so learners can
-- start "Message to support" conversations without an admin opening Messages first.
DROP POLICY IF EXISTS "Anyone can view admin mentor profiles for support" ON public.mentor_profiles;

CREATE POLICY "Anyone can view admin mentor profiles for support"
  ON public.mentor_profiles
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_roles ur
      WHERE ur.user_id = mentor_profiles.user_id AND ur.role = 'admin'
    )
  );

-- Return ALL support mentor profiles: users with role ADMIN.
-- "Message to support" for all users goes to any available admin (they all see support convos).
CREATE OR REPLACE FUNCTION public.get_support_mentor_profile()
RETURNS TABLE(id uuid, name text)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT mp.id, mp.name
  FROM mentor_profiles mp
  INNER JOIN user_roles ur ON ur.user_id = mp.user_id AND ur.role = 'admin'
  ORDER BY mp.created_at ASC;
$$;
