-- Enable realtime for user_roles table
-- This allows real-time subscriptions to detect INSERT, UPDATE, DELETE events

ALTER PUBLICATION supabase_realtime ADD TABLE public.user_roles;

-- Verify it's enabled
-- You can check in Supabase Dashboard > Database > Replication
-- The user_roles table should appear in the "Tables in publication" list
