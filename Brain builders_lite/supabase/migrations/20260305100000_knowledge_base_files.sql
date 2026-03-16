-- Storage bucket for knowledge base files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'knowledge-base-files',
  'knowledge-base-files',
  false,
  52428800, -- 50MB limit
  ARRAY[
    'application/pdf',
    'text/plain',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'audio/mpeg',
    'audio/wav',
    'audio/mp4'
  ]
)
ON CONFLICT (id) DO NOTHING;

-- RLS: mentors can upload/read their own files
CREATE POLICY "Mentors can upload knowledge base files"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'knowledge-base-files'
    AND auth.uid() IS NOT NULL
  );

CREATE POLICY "Mentors can read their own knowledge base files"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'knowledge-base-files'
    AND auth.uid() IS NOT NULL
  );

CREATE POLICY "Mentors can delete their own knowledge base files"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'knowledge-base-files'
    AND auth.uid() IS NOT NULL
  );

-- Add file_url column to mentor_knowledge_base for storing the uploaded file reference
ALTER TABLE mentor_knowledge_base
  ADD COLUMN IF NOT EXISTS file_url text,
  ADD COLUMN IF NOT EXISTS file_name text,
  ADD COLUMN IF NOT EXISTS file_type text;
