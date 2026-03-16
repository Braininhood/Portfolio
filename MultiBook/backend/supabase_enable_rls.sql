-- Enable Row Level Security (RLS) on all tables in public schema.
-- Run this in Supabase Dashboard -> SQL Editor.
-- This fixes: "Table public.xxx is exposed via API without RLS and contains potentially sensitive column(s)"
-- Django connects with the postgres user (bypasses RLS); Supabase API uses anon/authenticated (subject to RLS).
-- With RLS enabled and no permissive policies, the Supabase REST API cannot read/write these tables.

DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT schemaname, tablename
    FROM pg_tables
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format(
      'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
      r.schemaname,
      r.tablename
    );
    RAISE NOTICE 'RLS enabled on %.%', r.schemaname, r.tablename;
  END LOOP;
END $$;
