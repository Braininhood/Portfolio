-- Create mentor_questions table for Q&A system
CREATE TABLE public.mentor_questions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  question_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'submitted',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT valid_status CHECK (status IN ('submitted', 'answered', 'archived'))
);

-- Create mentor_video_answers table
CREATE TABLE public.mentor_video_answers (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  question_id UUID NOT NULL REFERENCES public.mentor_questions(id) ON DELETE CASCADE,
  video_url TEXT NOT NULL,
  video_file_name TEXT,
  duration_seconds INTEGER,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT unique_answer_per_question UNIQUE(question_id)
);

-- Add meeting link to bookings table
ALTER TABLE public.bookings
ADD COLUMN IF NOT EXISTS meeting_link TEXT,
ADD COLUMN IF NOT EXISTS meeting_platform TEXT,
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Enable RLS on new tables
ALTER TABLE public.mentor_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mentor_video_answers ENABLE ROW LEVEL SECURITY;

-- RLS policies for mentor_questions
CREATE POLICY "Users can view their own questions"
ON public.mentor_questions FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Mentors can view questions sent to them"
ON public.mentor_questions FOR SELECT
USING (EXISTS (
  SELECT 1 FROM public.mentor_profiles
  WHERE mentor_profiles.id = mentor_questions.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Users can create questions"
ON public.mentor_questions FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Mentors can update their questions"
ON public.mentor_questions FOR UPDATE
USING (EXISTS (
  SELECT 1 FROM public.mentor_profiles
  WHERE mentor_profiles.id = mentor_questions.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

-- RLS policies for mentor_video_answers
CREATE POLICY "Users can view answers to their questions"
ON public.mentor_video_answers FOR SELECT
USING (EXISTS (
  SELECT 1 FROM public.mentor_questions
  WHERE mentor_questions.id = mentor_video_answers.question_id
  AND mentor_questions.user_id = auth.uid()
));

CREATE POLICY "Mentors can view their own answers"
ON public.mentor_video_answers FOR SELECT
USING (EXISTS (
  SELECT 1 FROM public.mentor_questions
  JOIN public.mentor_profiles ON mentor_profiles.id = mentor_questions.mentor_id
  WHERE mentor_questions.id = mentor_video_answers.question_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Mentors can create answers"
ON public.mentor_video_answers FOR INSERT
WITH CHECK (EXISTS (
  SELECT 1 FROM public.mentor_questions
  JOIN public.mentor_profiles ON mentor_profiles.id = mentor_questions.mentor_id
  WHERE mentor_questions.id = mentor_video_answers.question_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Mentors can update their own answers"
ON public.mentor_video_answers FOR UPDATE
USING (EXISTS (
  SELECT 1 FROM public.mentor_questions
  JOIN public.mentor_profiles ON mentor_profiles.id = mentor_questions.mentor_id
  WHERE mentor_questions.id = mentor_video_answers.question_id
  AND mentor_profiles.user_id = auth.uid()
));

-- Create storage bucket for video answers
INSERT INTO storage.buckets (id, name, public)
VALUES ('mentor-videos', 'mentor-videos', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for video answers
CREATE POLICY "Anyone can view video answers"
ON storage.objects FOR SELECT
USING (bucket_id = 'mentor-videos');

CREATE POLICY "Mentors can upload video answers"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'mentor-videos' AND
  auth.uid() IS NOT NULL
);

CREATE POLICY "Mentors can update their video answers"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'mentor-videos' AND
  auth.uid() IS NOT NULL
);

CREATE POLICY "Mentors can delete their video answers"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'mentor-videos' AND
  auth.uid() IS NOT NULL
);

-- Add trigger for updated_at
CREATE TRIGGER update_mentor_questions_updated_at
BEFORE UPDATE ON public.mentor_questions
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();