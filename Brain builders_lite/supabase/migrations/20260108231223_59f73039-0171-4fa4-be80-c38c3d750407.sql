-- Fix mentor-videos storage bucket security
-- Make the bucket private instead of public
UPDATE storage.buckets 
SET public = false 
WHERE id = 'mentor-videos';

-- Drop existing overly permissive policies
DROP POLICY IF EXISTS "Anyone can view video answers" ON storage.objects;
DROP POLICY IF EXISTS "Mentors can upload video answers" ON storage.objects;
DROP POLICY IF EXISTS "Mentors can update their video answers" ON storage.objects;
DROP POLICY IF EXISTS "Mentors can delete their video answers" ON storage.objects;

-- Users can view videos for questions they asked
CREATE POLICY "Users can view videos for their questions"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'mentor-videos' AND
  EXISTS (
    SELECT 1 FROM mentor_video_answers mva
    JOIN mentor_questions mq ON mq.id = mva.question_id
    WHERE mva.video_url LIKE '%' || storage.objects.name || '%'
      AND mq.user_id = auth.uid()
  )
);

-- Mentors can view their own uploaded videos
CREATE POLICY "Mentors can view their videos"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'mentor-videos' AND
  EXISTS (
    SELECT 1 FROM mentor_video_answers mva
    JOIN mentor_questions mq ON mq.id = mva.question_id
    JOIN mentor_profiles mp ON mp.id = mq.mentor_id
    WHERE mva.video_url LIKE '%' || storage.objects.name || '%'
      AND mp.user_id = auth.uid()
  )
);

-- Only verified mentors can upload videos
CREATE POLICY "Mentors can upload videos"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'mentor-videos' AND
  EXISTS (
    SELECT 1 FROM mentor_profiles
    WHERE mentor_profiles.user_id = auth.uid()
  )
);

-- Mentors can update their own videos
CREATE POLICY "Mentors can update their videos"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'mentor-videos' AND
  EXISTS (
    SELECT 1 FROM mentor_video_answers mva
    JOIN mentor_questions mq ON mq.id = mva.question_id
    JOIN mentor_profiles mp ON mp.id = mq.mentor_id
    WHERE mva.video_url LIKE '%' || storage.objects.name || '%'
      AND mp.user_id = auth.uid()
  )
);

-- Mentors can delete their own videos
CREATE POLICY "Mentors can delete their videos"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'mentor-videos' AND
  EXISTS (
    SELECT 1 FROM mentor_video_answers mva
    JOIN mentor_questions mq ON mq.id = mva.question_id
    JOIN mentor_profiles mp ON mp.id = mq.mentor_id
    WHERE mva.video_url LIKE '%' || storage.objects.name || '%'
      AND mp.user_id = auth.uid()
  )
);