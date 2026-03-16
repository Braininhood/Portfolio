-- Fix get_mentor_learner_ids: add conversations + case-insensitive email
CREATE OR REPLACE FUNCTION public.get_mentor_learner_ids(p_mentor_id uuid)
RETURNS TABLE(learner_id uuid)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.mentor_profiles mp
    WHERE mp.id = p_mentor_id AND mp.user_id = auth.uid()
  ) AND NOT public.has_role(auth.uid(), 'admin') THEN
    RAISE EXCEPTION 'Unauthorized';
  END IF;

  RETURN QUERY
  SELECT b.user_id
  FROM public.bookings b
  WHERE b.mentor_id = p_mentor_id::text AND b.user_id IS NOT NULL

  UNION

  SELECT u.id
  FROM public.bookings b
  JOIN auth.users u ON LOWER(TRIM(u.email)) = LOWER(TRIM(b.user_email))
  WHERE b.mentor_id = p_mentor_id::text
    AND b.user_id IS NULL AND b.user_email IS NOT NULL

  UNION

  SELECT pp.buyer_id
  FROM public.product_purchases pp
  JOIN public.mentor_products mp ON mp.id = pp.product_id
  WHERE mp.mentor_id = p_mentor_id AND pp.status = 'completed'

  UNION

  SELECT c.user_id
  FROM public.conversations c
  WHERE c.mentor_id = p_mentor_id::text AND c.user_id IS NOT NULL;
END;
$$;
