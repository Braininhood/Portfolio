-- Add DELETE policy for conversations so users can delete their conversations
CREATE POLICY "Users and mentors can delete conversations" 
ON public.conversations 
FOR DELETE 
USING (
  (auth.uid() = user_id) OR 
  (EXISTS (
    SELECT 1 FROM mentor_profiles 
    WHERE mentor_profiles.id::text = conversations.mentor_id 
    AND mentor_profiles.user_id = auth.uid()
  ))
);