-- Set mentor role for a user by email (e.g. if they registered as mentor but role insert failed).
-- Run in Supabase Dashboard → SQL Editor.
-- Replace 'dommovoy@gmail.com' with the target email if needed.

INSERT INTO public.user_roles (user_id, role)
SELECT u.id, 'mentor'::public.app_role
FROM auth.users u
WHERE u.email = 'dommovoy@gmail.com'
  AND NOT EXISTS (
    SELECT 1 FROM public.user_roles ur
    WHERE ur.user_id = u.id AND ur.role = 'mentor'
  );

-- Optional: remove learner/user role if they were incorrectly set as learner
-- DELETE FROM public.user_roles ur
-- USING auth.users u
-- WHERE ur.user_id = u.id AND u.email = 'dommovoy@gmail.com' AND ur.role IN ('learner', 'user');
