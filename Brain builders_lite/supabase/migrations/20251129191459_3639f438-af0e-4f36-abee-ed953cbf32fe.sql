-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Storage buckets for avatar assets
INSERT INTO storage.buckets (id, name, public) 
VALUES ('avatar-photos', 'avatar-photos', true),
       ('avatar-voices', 'avatar-voices', false)
ON CONFLICT (id) DO NOTHING;

-- Mentor avatars table
CREATE TABLE mentor_avatars (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mentor_id UUID NOT NULL REFERENCES mentor_profiles(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft',
  avatar_name TEXT,
  bio_summary TEXT,
  expertise_areas TEXT[],
  personality_traits TEXT[],
  photo_urls TEXT[],
  voice_sample_url TEXT,
  training_completed_at TIMESTAMPTZ,
  last_trained_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Knowledge base for RAG
CREATE TABLE mentor_avatar_knowledge (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  avatar_id UUID NOT NULL REFERENCES mentor_avatars(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  content_type TEXT NOT NULL,
  metadata JSONB,
  embedding vector(768),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User conversations with avatars
CREATE TABLE avatar_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  avatar_id UUID NOT NULL REFERENCES mentor_avatars(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Avatar chat messages
CREATE TABLE avatar_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES avatar_conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index for similarity search
CREATE INDEX mentor_avatar_knowledge_embedding_idx ON mentor_avatar_knowledge 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RLS policies
ALTER TABLE mentor_avatars ENABLE ROW LEVEL SECURITY;
ALTER TABLE mentor_avatar_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE avatar_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE avatar_messages ENABLE ROW LEVEL SECURITY;

-- Mentor avatar policies
CREATE POLICY "Mentors can view their own avatars"
  ON mentor_avatars FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM mentor_profiles
    WHERE mentor_profiles.id = mentor_avatars.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  ));

CREATE POLICY "Mentors can create their own avatars"
  ON mentor_avatars FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM mentor_profiles
    WHERE mentor_profiles.id = mentor_avatars.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  ));

CREATE POLICY "Mentors can update their own avatars"
  ON mentor_avatars FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM mentor_profiles
    WHERE mentor_profiles.id = mentor_avatars.mentor_id
    AND mentor_profiles.user_id = auth.uid()
  ));

CREATE POLICY "Anyone can view ready avatars"
  ON mentor_avatars FOR SELECT
  USING (status = 'ready');

-- Knowledge base policies
CREATE POLICY "Mentors can manage their avatar knowledge"
  ON mentor_avatar_knowledge FOR ALL
  USING (EXISTS (
    SELECT 1 FROM mentor_avatars ma
    JOIN mentor_profiles mp ON mp.id = ma.mentor_id
    WHERE ma.id = mentor_avatar_knowledge.avatar_id
    AND mp.user_id = auth.uid()
  ));

-- Conversation policies
CREATE POLICY "Users can view their own avatar conversations"
  ON avatar_conversations FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can create avatar conversations"
  ON avatar_conversations FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their conversations"
  ON avatar_conversations FOR UPDATE
  USING (user_id = auth.uid());

-- Message policies
CREATE POLICY "Users can view messages in their conversations"
  ON avatar_messages FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM avatar_conversations
    WHERE avatar_conversations.id = avatar_messages.conversation_id
    AND avatar_conversations.user_id = auth.uid()
  ));

CREATE POLICY "Users can create messages in their conversations"
  ON avatar_messages FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM avatar_conversations
    WHERE avatar_conversations.id = avatar_messages.conversation_id
    AND avatar_conversations.user_id = auth.uid()
  ));

-- Storage policies for avatar photos
CREATE POLICY "Anyone can view avatar photos"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'avatar-photos');

CREATE POLICY "Mentors can upload avatar photos"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'avatar-photos' AND auth.role() = 'authenticated');

CREATE POLICY "Mentors can update their avatar photos"
  ON storage.objects FOR UPDATE
  USING (bucket_id = 'avatar-photos' AND auth.role() = 'authenticated');

CREATE POLICY "Mentors can delete their avatar photos"
  ON storage.objects FOR DELETE
  USING (bucket_id = 'avatar-photos' AND auth.role() = 'authenticated');

-- Storage policies for voice samples
CREATE POLICY "Mentors can upload voice samples"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'avatar-voices' AND auth.role() = 'authenticated');

CREATE POLICY "Mentors can access their voice samples"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'avatar-voices' AND auth.role() = 'authenticated');

CREATE POLICY "Mentors can update their voice samples"
  ON storage.objects FOR UPDATE
  USING (bucket_id = 'avatar-voices' AND auth.role() = 'authenticated');

CREATE POLICY "Mentors can delete their voice samples"
  ON storage.objects FOR DELETE
  USING (bucket_id = 'avatar-voices' AND auth.role() = 'authenticated');

-- Triggers
CREATE TRIGGER update_mentor_avatars_updated_at
  BEFORE UPDATE ON mentor_avatars
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_avatar_conversations_updated_at
  BEFORE UPDATE ON avatar_conversations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();