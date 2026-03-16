-- Allow users to see their own mentor profile (so admin can create and read back is_active: false).
-- Fixes: "new row violates row-level security" when admin creates profile and .select() runs.

CREATE POLICY "Users can view own mentor profile"
  ON public.mentor_profiles
  FOR SELECT
  USING (auth.uid() = user_id);
