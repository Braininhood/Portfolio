-- Allow new users to assign themselves mentor or learner role once (no existing roles).
-- Runs in a separate migration so enum values from 20260222100000 are committed first.
CREATE POLICY "Users can insert own role mentor or learner when no roles"
  ON public.user_roles
  FOR INSERT
  WITH CHECK (
    auth.uid() = user_id
    AND role IN ('mentor', 'learner')
    AND NOT EXISTS (
      SELECT 1 FROM public.user_roles ur WHERE ur.user_id = auth.uid()
    )
  );
