-- Create an admin account: grant admin role to an existing user.
-- Run in Supabase Dashboard → SQL Editor.
--
-- Step 1: Ensure the user exists (sign up at /auth/learner or add in Dashboard → Authentication → Users).
-- Step 2: Replace 'admin@example.com' with their email below and run.

INSERT INTO public.user_roles (user_id, role)
SELECT u.id, 'admin'::public.app_role
FROM auth.users u
WHERE u.email = 'admin@example.com'
  AND NOT EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = u.id AND ur.role = 'admin'
  );

-- Check: list admins
-- SELECT u.email, ur.role
-- FROM auth.users u
-- JOIN public.user_roles ur ON ur.user_id = u.id
-- WHERE ur.role = 'admin';
