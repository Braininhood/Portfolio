-- Tables not present in current schema: mentor_services, product_variants, stripe_accounts, transactions.
-- Aligns documentation with DB and supports future platform fee / Stripe Connect.

-- 1. mentor_services (offer types per mentor: duration, price, delivery)
CREATE TABLE public.mentor_services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  duration_minutes INTEGER NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'USD',
  delivery_method TEXT NOT NULL,
  requires_preparation BOOLEAN DEFAULT false,
  preparation_instructions TEXT,
  advance_booking_hours INTEGER DEFAULT 48,
  max_participants INTEGER DEFAULT 1,
  cancellation_deadline_hours INTEGER DEFAULT 24,
  refund_policy JSONB,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mentor_services_mentor ON public.mentor_services(mentor_id);
CREATE INDEX idx_mentor_services_active ON public.mentor_services(is_active);
ALTER TABLE public.mentor_services ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view active mentor_services"
  ON public.mentor_services FOR SELECT
  USING (is_active = true);

CREATE POLICY "Mentors can manage their own mentor_services"
  ON public.mentor_services FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = mentor_services.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = mentor_services.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

-- 2. product_variants (per mentor_products: language/format variants)
CREATE TABLE public.product_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES public.mentor_products(id) ON DELETE CASCADE,
  language TEXT NOT NULL,
  format TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size_bytes BIGINT,
  price DECIMAL(10,2),
  is_auto_generated BOOLEAN DEFAULT false,
  generation_status TEXT,
  reviewed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_product_variants_product ON public.product_variants(product_id);
CREATE INDEX idx_product_variants_language ON public.product_variants(language);
ALTER TABLE public.product_variants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view product_variants for active products"
  ON public.product_variants FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_products
      WHERE mentor_products.id = product_variants.product_id
      AND mentor_products.is_active = true
    )
  );

CREATE POLICY "Mentors can manage variants of their products"
  ON public.product_variants FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_products mp
      JOIN public.mentor_profiles m ON m.id = mp.mentor_id
      WHERE mp.id = product_variants.product_id
      AND m.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.mentor_products mp
      JOIN public.mentor_profiles m ON m.id = mp.mentor_id
      WHERE mp.id = product_variants.product_id
      AND m.user_id = auth.uid()
    )
  );

-- 3. stripe_accounts (Stripe Connect per mentor)
CREATE TABLE public.stripe_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mentor_id UUID NOT NULL UNIQUE REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  stripe_account_id TEXT NOT NULL UNIQUE,
  account_status TEXT,
  onboarding_completed BOOLEAN DEFAULT false,
  charges_enabled BOOLEAN DEFAULT false,
  payouts_enabled BOOLEAN DEFAULT false,
  payout_schedule TEXT DEFAULT 'weekly',
  minimum_payout_amount DECIMAL(10,2) DEFAULT 50.00,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_accounts_mentor ON public.stripe_accounts(mentor_id);
ALTER TABLE public.stripe_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Mentors can view their own stripe_accounts"
  ON public.stripe_accounts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = stripe_accounts.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

CREATE POLICY "Mentors can insert their own stripe_accounts"
  ON public.stripe_accounts FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = stripe_accounts.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

CREATE POLICY "Mentors can update their own stripe_accounts"
  ON public.stripe_accounts FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = stripe_accounts.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

-- 4. transactions (platform fee, payouts; complements product_purchases/bookings)
CREATE TABLE public.transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  related_id UUID,
  gross_amount DECIMAL(10,2) NOT NULL,
  platform_fee DECIMAL(10,2) NOT NULL,
  stripe_fee DECIMAL(10,2) NOT NULL,
  net_amount DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'USD',
  stripe_payment_intent_id TEXT,
  stripe_charge_id TEXT,
  stripe_transfer_id TEXT,
  status TEXT NOT NULL,
  payout_date DATE,
  payout_status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_mentor ON public.transactions(mentor_id);
CREATE INDEX idx_transactions_user ON public.transactions(user_id);
CREATE INDEX idx_transactions_status ON public.transactions(status);
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Mentors can view their own transactions"
  ON public.transactions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.mentor_profiles
      WHERE mentor_profiles.id = transactions.mentor_id
      AND mentor_profiles.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can view their own transactions"
  ON public.transactions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can manage transactions"
  ON public.transactions FOR ALL
  USING (public.has_role(auth.uid(), 'admin'))
  WITH CHECK (public.has_role(auth.uid(), 'admin'));
