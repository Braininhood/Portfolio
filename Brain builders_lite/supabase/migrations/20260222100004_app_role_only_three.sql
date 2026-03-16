-- Restrict app_role to only admin, mentor, learner (remove moderator, user).
-- Admin role is preserved. Existing moderator/user rows are converted to learner.
-- Step 1: Drop all policies that depend on has_role(uuid, app_role)

DROP POLICY IF EXISTS "Only admins can delete mentor profiles" ON public.mentor_profiles;
DROP POLICY IF EXISTS "Admins can view all bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can view all mentor_questions" ON public.mentor_questions;
DROP POLICY IF EXISTS "Admins can view all product_purchases" ON public.product_purchases;
DROP POLICY IF EXISTS "Admins can view all push_subscriptions" ON public.push_subscriptions;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can insert bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can update bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can delete bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can update profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can insert mentor_questions" ON public.mentor_questions;
DROP POLICY IF EXISTS "Admins can update mentor_questions" ON public.mentor_questions;
DROP POLICY IF EXISTS "Admins can delete mentor_questions" ON public.mentor_questions;
DROP POLICY IF EXISTS "Admins can update product_purchases" ON public.product_purchases;
DROP POLICY IF EXISTS "Admins can delete product_purchases" ON public.product_purchases;
DROP POLICY IF EXISTS "Admins can delete push_subscriptions" ON public.push_subscriptions;

-- Step 2: Drop function that depends on app_role
DROP FUNCTION IF EXISTS public.has_role(UUID, public.app_role);

-- Step 2b: Drop user_roles policies that depend on column role (so we can drop/rename column)
DROP POLICY IF EXISTS "Only admins can insert roles" ON public.user_roles;
DROP POLICY IF EXISTS "Only admins can update roles" ON public.user_roles;
DROP POLICY IF EXISTS "Only admins can delete roles" ON public.user_roles;
DROP POLICY IF EXISTS "Users can insert own role mentor or learner when no roles" ON public.user_roles;

-- Step 3: New enum with only the 3 roles (admin, mentor, learner)
CREATE TYPE public.app_role_new AS ENUM ('admin', 'mentor', 'learner');

ALTER TABLE public.user_roles ADD COLUMN role_new public.app_role_new;

UPDATE public.user_roles
SET role_new = CASE role::text
  WHEN 'admin' THEN 'admin'::public.app_role_new
  WHEN 'mentor' THEN 'mentor'::public.app_role_new
  WHEN 'learner' THEN 'learner'::public.app_role_new
  ELSE 'learner'::public.app_role_new
END;

ALTER TABLE public.user_roles DROP COLUMN role;
ALTER TABLE public.user_roles RENAME COLUMN role_new TO role;

DROP TYPE public.app_role;
ALTER TYPE public.app_role_new RENAME TO app_role;

-- Step 4: Recreate has_role for new enum (admin role unchanged)
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
  )
$$;

-- Step 4b: Recreate user_roles policies (role column is now new app_role type)
CREATE POLICY "Only admins can insert roles"
  ON public.user_roles FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Only admins can update roles"
  ON public.user_roles FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Only admins can delete roles"
  ON public.user_roles FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Users can insert own role mentor or learner when no roles"
  ON public.user_roles FOR INSERT
  WITH CHECK (
    auth.uid() = user_id
    AND role IN ('mentor', 'learner')
    AND NOT EXISTS (
      SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid()
    )
  );

-- Step 5: Recreate admin policies
CREATE POLICY "Only admins can delete mentor profiles"
  ON public.mentor_profiles FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all bookings"
  ON public.bookings FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all mentor_questions"
  ON public.mentor_questions FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all product_purchases"
  ON public.product_purchases FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all push_subscriptions"
  ON public.push_subscriptions FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all profiles"
  ON public.profiles FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert bookings"
  ON public.bookings FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update bookings"
  ON public.bookings FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete bookings"
  ON public.bookings FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update profiles"
  ON public.profiles FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert mentor_questions"
  ON public.mentor_questions FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update mentor_questions"
  ON public.mentor_questions FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete mentor_questions"
  ON public.mentor_questions FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update product_purchases"
  ON public.product_purchases FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete product_purchases"
  ON public.product_purchases FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete push_subscriptions"
  ON public.push_subscriptions FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));
