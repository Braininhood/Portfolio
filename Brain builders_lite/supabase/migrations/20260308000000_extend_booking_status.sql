-- Extend bookings status to support completed, failed, refunded
-- Required for: Stripe webhook (failed/refunded), mentor mark-complete, admin UI

ALTER TABLE public.bookings
  DROP CONSTRAINT IF EXISTS bookings_status_check;

ALTER TABLE public.bookings
  ADD CONSTRAINT bookings_status_check CHECK (
    status IN ('pending', 'confirmed', 'cancelled', 'completed', 'failed', 'refunded')
  );

COMMENT ON COLUMN public.bookings.status IS 
  'pending=awaiting payment, confirmed=paid, cancelled=user/admin cancelled, completed=session done, failed=payment failed, refunded=Stripe refund';
