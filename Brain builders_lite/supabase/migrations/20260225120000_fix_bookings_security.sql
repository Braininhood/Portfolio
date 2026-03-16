-- Fix bookings table security issues
-- Add user_id column and proper RLS policies

-- 1. Add user_id column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'bookings'
    AND column_name = 'user_id'
  ) THEN
    ALTER TABLE public.bookings ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
  END IF;
END $$;

-- 2. Migrate existing data: match user_email to auth.users.email
UPDATE public.bookings
SET user_id = (
  SELECT id FROM auth.users WHERE email = bookings.user_email
)
WHERE user_id IS NULL AND user_email IS NOT NULL;

-- 3. Drop old policies (they might already exist from previous runs)
DROP POLICY IF EXISTS "Users can view their own bookings" ON public.bookings;
DROP POLICY IF EXISTS "Anyone can create bookings" ON public.bookings;
DROP POLICY IF EXISTS "Users can update their own bookings" ON public.bookings;
DROP POLICY IF EXISTS "Authenticated users can create bookings" ON public.bookings;
DROP POLICY IF EXISTS "Users can delete their own bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can view all bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins can manage all bookings" ON public.bookings;
DROP POLICY IF EXISTS "Mentors can view their bookings" ON public.bookings;

-- 4. Create secure RLS policies
CREATE POLICY "Users can view their own bookings"
ON public.bookings
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Authenticated users can create bookings"
ON public.bookings
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bookings"
ON public.bookings
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bookings"
ON public.bookings
FOR DELETE
USING (auth.uid() = user_id);

-- 5. Admin policies
CREATE POLICY "Admins can view all bookings"
ON public.bookings
FOR SELECT
USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can manage all bookings"
ON public.bookings
FOR ALL
USING (public.has_role(auth.uid(), 'admin'))
WITH CHECK (public.has_role(auth.uid(), 'admin'));

-- 6. Mentor can view bookings for their services
CREATE POLICY "Mentors can view their bookings"
ON public.bookings
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = bookings.mentor_id::uuid
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- 7. Add index for better performance
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON public.bookings(user_id);

-- 8. Add comment for documentation
COMMENT ON COLUMN public.bookings.user_id IS 'References auth.users(id). Required for RLS. Replaces user_email for security.';
COMMENT ON COLUMN public.bookings.user_email IS 'Deprecated. Kept for backward compatibility. Use user_id instead.';
