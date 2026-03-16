-- Allow admins to start conversations with any user, as the mentor participant.
-- This assumes the admin account has a mentor_profile and uses its mentor_profiles.id as conversations.mentor_id.

CREATE POLICY "Admins can create conversations as mentor"
  ON public.conversations
  FOR INSERT
  WITH CHECK (
    public.has_role(auth.uid(), 'admin')
    AND EXISTS (
      SELECT 1
      FROM public.mentor_profiles mp
      WHERE mp.id::text = conversations.mentor_id
        AND mp.user_id = auth.uid()
    )
  );

