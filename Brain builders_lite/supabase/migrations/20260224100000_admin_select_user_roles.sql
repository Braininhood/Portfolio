-- Allow admins to read all user_roles so Admin Learners page can show and update roles.
CREATE POLICY "Admins can view all user_roles"
  ON public.user_roles
  FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));
