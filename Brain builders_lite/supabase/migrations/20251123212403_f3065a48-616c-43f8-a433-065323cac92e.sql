-- Create storage bucket for message attachments
INSERT INTO storage.buckets (id, name, public)
VALUES ('message-attachments', 'message-attachments', true);

-- Create RLS policies for message attachments bucket
CREATE POLICY "Users can view attachments in their conversations"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'message-attachments' AND
  EXISTS (
    SELECT 1 FROM conversations
    WHERE conversations.user_id = auth.uid()
    AND storage.objects.name LIKE conversations.id || '/%'
  )
);

CREATE POLICY "Users can upload attachments to their conversations"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'message-attachments' AND
  EXISTS (
    SELECT 1 FROM conversations
    WHERE conversations.user_id = auth.uid()
    AND storage.objects.name LIKE conversations.id || '/%'
  )
);

CREATE POLICY "Users can delete their own attachments"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'message-attachments' AND
  EXISTS (
    SELECT 1 FROM conversations
    WHERE conversations.user_id = auth.uid()
    AND storage.objects.name LIKE conversations.id || '/%'
  )
);

-- Add file_url and file_name columns to messages table
ALTER TABLE public.messages 
ADD COLUMN file_url TEXT,
ADD COLUMN file_name TEXT,
ADD COLUMN file_type TEXT;