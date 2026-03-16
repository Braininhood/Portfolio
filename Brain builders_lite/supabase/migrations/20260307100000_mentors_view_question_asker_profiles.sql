-- Allow mentors to view profiles of users who asked them questions
-- Fixes "Anonymous" showing instead of learner names on Questions tab

CREATE POLICY "Mentors can view profiles of their question askers"
  ON public.profiles FOR SELECT
  USING (
    id IN (
      SELECT mq.user_id
      FROM public.mentor_questions mq
      JOIN public.mentor_profiles mp ON mp.id = mq.mentor_id
      WHERE mp.user_id = auth.uid()
        AND mq.user_id IS NOT NULL
    )
  );
