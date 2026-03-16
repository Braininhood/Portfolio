-- Enable REPLICA IDENTITY FULL for messages table for proper realtime support with RLS
ALTER TABLE public.messages REPLICA IDENTITY FULL;

-- Also enable for conversations and message_read_receipts for complete realtime support  
ALTER TABLE public.conversations REPLICA IDENTITY FULL;
ALTER TABLE public.message_read_receipts REPLICA IDENTITY FULL;

-- Ensure conversations is in the realtime publication
ALTER PUBLICATION supabase_realtime ADD TABLE public.conversations;