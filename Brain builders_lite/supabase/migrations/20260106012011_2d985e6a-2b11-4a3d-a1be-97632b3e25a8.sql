-- Ensure idempotency for purchases created/verified by Stripe session
-- A unique index is required for reliable upserts on stripe_session_id.
CREATE UNIQUE INDEX IF NOT EXISTS product_purchases_stripe_session_id_uniq
ON public.product_purchases (stripe_session_id)
WHERE stripe_session_id IS NOT NULL;