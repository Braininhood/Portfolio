-- Add mentor and learner to app_role enum.
-- Must be in a separate migration: new enum values cannot be used in the same transaction.
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'mentor';
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'learner';
