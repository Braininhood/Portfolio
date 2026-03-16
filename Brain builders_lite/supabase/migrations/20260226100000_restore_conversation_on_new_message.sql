-- Restore soft-deleted conversations when a new message is sent
-- If mentor/learner/support sends a message after someone "deleted" the conversation,
-- the conversation reappears in everyone's list.

CREATE OR REPLACE FUNCTION public.restore_conversation_on_new_message()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  DELETE FROM public.conversation_deletions
  WHERE conversation_id = NEW.conversation_id;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trigger_restore_conversation_on_new_message ON public.messages;
CREATE TRIGGER trigger_restore_conversation_on_new_message
  AFTER INSERT ON public.messages
  FOR EACH ROW
  EXECUTE FUNCTION public.restore_conversation_on_new_message();

COMMENT ON FUNCTION public.restore_conversation_on_new_message() IS
  'When any message is inserted, clear conversation_deletions for that conversation so it reappears for users who had hidden it.';
