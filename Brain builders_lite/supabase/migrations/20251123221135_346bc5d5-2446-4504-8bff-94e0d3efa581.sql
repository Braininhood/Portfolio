-- Add preferred_language column to profiles table
ALTER TABLE public.profiles 
ADD COLUMN preferred_language TEXT DEFAULT NULL;

-- Add index for faster lookups
CREATE INDEX idx_profiles_preferred_language ON public.profiles(preferred_language) WHERE preferred_language IS NOT NULL;