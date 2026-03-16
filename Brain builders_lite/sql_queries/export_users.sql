-- Export all users with their credentials information
-- NOTE: Passwords are hashed and cannot be exported. This shows emails and roles only.

SELECT 
  u.id as user_id,
  u.email,
  p.full_name,
  u.created_at as registered_at,
  string_agg(DISTINCT ur.role::text, ', ' ORDER BY ur.role::text) as roles,
  CASE 
    WHEN EXISTS (SELECT 1 FROM public.mentor_profiles mp WHERE mp.user_id = u.id) 
    THEN 'Yes' ELSE 'No' 
  END as has_mentor_profile
FROM auth.users u
LEFT JOIN public.profiles p ON p.id = u.id
LEFT JOIN public.user_roles ur ON ur.user_id = u.id
GROUP BY u.id, u.email, p.full_name, u.created_at
ORDER BY u.created_at DESC;
