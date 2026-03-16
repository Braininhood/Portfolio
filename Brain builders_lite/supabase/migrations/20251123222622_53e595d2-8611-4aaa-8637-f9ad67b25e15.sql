-- Create mentor_profiles table
CREATE TABLE public.mentor_profiles (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  title TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('Business', 'Tech', 'Creators')),
  image_url TEXT,
  rating DECIMAL(2,1) DEFAULT 0.0 CHECK (rating >= 0 AND rating <= 5),
  review_count INTEGER DEFAULT 0,
  price DECIMAL(10,2) NOT NULL,
  bio TEXT NOT NULL,
  full_bio TEXT NOT NULL,
  expertise TEXT[] NOT NULL,
  languages TEXT[] NOT NULL,
  availability TEXT NOT NULL,
  experience TEXT NOT NULL,
  education TEXT NOT NULL,
  certifications TEXT[],
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.mentor_profiles ENABLE ROW LEVEL SECURITY;

-- Public can view active mentors
CREATE POLICY "Anyone can view active mentor profiles"
ON public.mentor_profiles
FOR SELECT
USING (is_active = true);

-- Mentors can update their own profile
CREATE POLICY "Mentors can update their own profile"
ON public.mentor_profiles
FOR UPDATE
USING (auth.uid() = user_id);

-- Admins can insert mentor profiles (will need admin role setup)
CREATE POLICY "Authenticated users can insert mentor profiles"
ON public.mentor_profiles
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Create mentor_reviews table
CREATE TABLE public.mentor_reviews (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID REFERENCES public.mentor_profiles(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  user_name TEXT NOT NULL,
  user_avatar TEXT,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.mentor_reviews ENABLE ROW LEVEL SECURITY;

-- Anyone can view reviews
CREATE POLICY "Anyone can view reviews"
ON public.mentor_reviews
FOR SELECT
USING (true);

-- Users can create reviews
CREATE POLICY "Users can create their own reviews"
ON public.mentor_reviews
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Users can update their own reviews
CREATE POLICY "Users can update their own reviews"
ON public.mentor_reviews
FOR UPDATE
USING (auth.uid() = user_id);

-- Users can delete their own reviews
CREATE POLICY "Users can delete their own reviews"
ON public.mentor_reviews
FOR DELETE
USING (auth.uid() = user_id);

-- Create mentor_courses table
CREATE TABLE public.mentor_courses (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID REFERENCES public.mentor_profiles(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  duration TEXT NOT NULL,
  lessons INTEGER NOT NULL,
  level TEXT NOT NULL CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
  thumbnail_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.mentor_courses ENABLE ROW LEVEL SECURITY;

-- Anyone can view active courses
CREATE POLICY "Anyone can view active courses"
ON public.mentor_courses
FOR SELECT
USING (is_active = true);

-- Mentors can manage their own courses
CREATE POLICY "Mentors can manage their own courses"
ON public.mentor_courses
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_courses.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- Create mentor_time_slots table
CREATE TABLE public.mentor_time_slots (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID REFERENCES public.mentor_profiles(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  time TIME NOT NULL,
  is_available BOOLEAN DEFAULT true,
  booking_id UUID REFERENCES public.bookings(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(mentor_id, date, time)
);

-- Enable RLS
ALTER TABLE public.mentor_time_slots ENABLE ROW LEVEL SECURITY;

-- Anyone can view available time slots
CREATE POLICY "Anyone can view time slots"
ON public.mentor_time_slots
FOR SELECT
USING (true);

-- Mentors can manage their own time slots
CREATE POLICY "Mentors can manage their own time slots"
ON public.mentor_time_slots
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.mentor_profiles
    WHERE mentor_profiles.id = mentor_time_slots.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_mentor_profiles_updated_at
BEFORE UPDATE ON public.mentor_profiles
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_mentor_reviews_updated_at
BEFORE UPDATE ON public.mentor_reviews
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_mentor_courses_updated_at
BEFORE UPDATE ON public.mentor_courses
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_mentor_time_slots_updated_at
BEFORE UPDATE ON public.mentor_time_slots
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();

-- Create function to update mentor rating
CREATE OR REPLACE FUNCTION public.update_mentor_rating()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  UPDATE public.mentor_profiles
  SET 
    rating = (
      SELECT COALESCE(AVG(rating), 0)
      FROM public.mentor_reviews
      WHERE mentor_id = NEW.mentor_id
    ),
    review_count = (
      SELECT COUNT(*)
      FROM public.mentor_reviews
      WHERE mentor_id = NEW.mentor_id
    )
  WHERE id = NEW.mentor_id;
  RETURN NEW;
END;
$$;

-- Trigger to update mentor rating when review is added/updated/deleted
CREATE TRIGGER update_mentor_rating_on_review_insert
AFTER INSERT ON public.mentor_reviews
FOR EACH ROW
EXECUTE FUNCTION public.update_mentor_rating();

CREATE TRIGGER update_mentor_rating_on_review_update
AFTER UPDATE ON public.mentor_reviews
FOR EACH ROW
EXECUTE FUNCTION public.update_mentor_rating();

CREATE TRIGGER update_mentor_rating_on_review_delete
AFTER DELETE ON public.mentor_reviews
FOR EACH ROW
EXECUTE FUNCTION public.update_mentor_rating();