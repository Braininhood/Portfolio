-- Run this in Supabase Dashboard → SQL Editor to check if a user is a mentor.
-- Replace the email with the one you want to check.

-- 1) Roles from user_roles (mentor, learner, admin, etc.)
SELECT
  u.id AS user_id,
  u.email,
  u.created_at AS user_created,
  ur.role,
  ur.created_at AS role_created
FROM auth.users u
LEFT JOIN public.user_roles ur ON u.id = ur.user_id
WHERE u.email = 'dommovoy@gmail.com';

-- 2) Mentor profile (if they have one, they can use mentor features)
SELECT
  u.email,
  mp.id AS mentor_profile_id,
  mp.name AS mentor_name,
  mp.username
FROM auth.users u
LEFT JOIN public.mentor_profiles mp ON u.id = mp.user_id
WHERE u.email = 'dommovoy@gmail.com';

-- Summary: user is "mentor" if (1) has role = 'mentor' in user_roles and/or (2) has a row in mentor_profiles.
