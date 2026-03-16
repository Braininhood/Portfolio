-- Add RLS policies for mentors to view and update their bookings

-- Policy 1: Allow mentors to view bookings assigned to them
CREATE POLICY "Mentors can view their bookings"
  ON public.bookings
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id::text = bookings.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

-- Policy 2: Allow mentors to update their bookings (meeting link, status, notes)
CREATE POLICY "Mentors can update their bookings"
  ON public.bookings
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id::text = bookings.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id::text = bookings.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );