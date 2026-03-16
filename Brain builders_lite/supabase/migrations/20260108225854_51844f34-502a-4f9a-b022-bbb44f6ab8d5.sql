-- Fix conversations RLS policies to include mentors
-- First, drop the existing restrictive policies
DROP POLICY IF EXISTS "Users can view their own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can create conversations" ON conversations;
DROP POLICY IF EXISTS "Users can update their own conversations" ON conversations;
DROP POLICY IF EXISTS "Users and mentors can view conversations" ON conversations;
DROP POLICY IF EXISTS "Users and mentors can update conversations" ON conversations;

-- Create new policies that include both users and mentors
-- Users can view conversations where they are the user OR they are the mentor
CREATE POLICY "Users and mentors can view conversations" ON conversations
FOR SELECT USING (
  auth.uid() = user_id OR 
  EXISTS (
    SELECT 1 FROM mentor_profiles 
    WHERE mentor_profiles.id::text = conversations.mentor_id 
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- Users can create conversations as themselves
CREATE POLICY "Users can create conversations" ON conversations
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users and mentors can update conversations they participate in
CREATE POLICY "Users and mentors can update conversations" ON conversations
FOR UPDATE USING (
  auth.uid() = user_id OR 
  EXISTS (
    SELECT 1 FROM mentor_profiles 
    WHERE mentor_profiles.id::text = conversations.mentor_id 
    AND mentor_profiles.user_id = auth.uid()
  )
);

-- Fix messages RLS policies to include mentors
DROP POLICY IF EXISTS "Users can view messages in their conversations" ON messages;
DROP POLICY IF EXISTS "Users can send messages in their conversations" ON messages;
DROP POLICY IF EXISTS "Users can update messages they sent" ON messages;
DROP POLICY IF EXISTS "Users can delete their own messages" ON messages;
DROP POLICY IF EXISTS "Users and mentors can view messages" ON messages;
DROP POLICY IF EXISTS "Users and mentors can send messages" ON messages;
DROP POLICY IF EXISTS "Participants can update messages" ON messages;

-- Create new message policies that include mentors
-- Users and mentors can view messages in their conversations
CREATE POLICY "Users and mentors can view messages" ON messages
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM conversations 
    WHERE conversations.id = messages.conversation_id 
    AND (
      conversations.user_id = auth.uid() OR 
      EXISTS (
        SELECT 1 FROM mentor_profiles 
        WHERE mentor_profiles.id::text = conversations.mentor_id 
        AND mentor_profiles.user_id = auth.uid()
      )
    )
  )
);

-- Users and mentors can send messages in their conversations
CREATE POLICY "Users and mentors can send messages" ON messages
FOR INSERT WITH CHECK (
  auth.uid() = sender_id AND
  EXISTS (
    SELECT 1 FROM conversations 
    WHERE conversations.id = messages.conversation_id 
    AND (
      conversations.user_id = auth.uid() OR 
      EXISTS (
        SELECT 1 FROM mentor_profiles 
        WHERE mentor_profiles.id::text = conversations.mentor_id 
        AND mentor_profiles.user_id = auth.uid()
      )
    )
  )
);

-- Participants can update messages in their conversations (for read receipts, delivery status)
-- Sender can update their own messages (for editing content)
CREATE POLICY "Participants can update messages" ON messages
FOR UPDATE USING (
  -- Sender can edit their own message
  auth.uid() = sender_id OR
  -- Participants can update read status/delivery status for messages in their conversations
  EXISTS (
    SELECT 1 FROM conversations 
    WHERE conversations.id = messages.conversation_id 
    AND (
      conversations.user_id = auth.uid() OR 
      EXISTS (
        SELECT 1 FROM mentor_profiles 
        WHERE mentor_profiles.id::text = conversations.mentor_id 
        AND mentor_profiles.user_id = auth.uid()
      )
    )
  )
);

-- Users can only delete their own messages
CREATE POLICY "Users can delete their own messages" ON messages
FOR DELETE USING (auth.uid() = sender_id);