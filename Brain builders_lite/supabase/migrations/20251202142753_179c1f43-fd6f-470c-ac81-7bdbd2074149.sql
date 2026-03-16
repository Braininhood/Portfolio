-- Create table for digital products
CREATE TABLE public.mentor_products (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  mentor_id UUID NOT NULL REFERENCES public.mentor_profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  price NUMERIC NOT NULL CHECK (price >= 0),
  file_url TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  preview_image_url TEXT,
  sales_count INTEGER NOT NULL DEFAULT 0,
  total_earnings NUMERIC NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create table for product purchases
CREATE TABLE public.product_purchases (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  product_id UUID NOT NULL REFERENCES public.mentor_products(id) ON DELETE CASCADE,
  buyer_id UUID NOT NULL,
  buyer_email TEXT NOT NULL,
  amount NUMERIC NOT NULL,
  stripe_payment_intent_id TEXT,
  stripe_session_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.mentor_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_purchases ENABLE ROW LEVEL SECURITY;

-- RLS policies for mentor_products
CREATE POLICY "Anyone can view active products"
ON public.mentor_products FOR SELECT
USING (is_active = true);

CREATE POLICY "Mentors can view their own products"
ON public.mentor_products FOR SELECT
USING (EXISTS (
  SELECT 1 FROM mentor_profiles
  WHERE mentor_profiles.id = mentor_products.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Mentors can create their own products"
ON public.mentor_products FOR INSERT
WITH CHECK (EXISTS (
  SELECT 1 FROM mentor_profiles
  WHERE mentor_profiles.id = mentor_products.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Mentors can update their own products"
ON public.mentor_products FOR UPDATE
USING (EXISTS (
  SELECT 1 FROM mentor_profiles
  WHERE mentor_profiles.id = mentor_products.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Mentors can delete their own products"
ON public.mentor_products FOR DELETE
USING (EXISTS (
  SELECT 1 FROM mentor_profiles
  WHERE mentor_profiles.id = mentor_products.mentor_id
  AND mentor_profiles.user_id = auth.uid()
));

-- RLS policies for product_purchases
CREATE POLICY "Buyers can view their own purchases"
ON public.product_purchases FOR SELECT
USING (buyer_id = auth.uid());

CREATE POLICY "Mentors can view purchases of their products"
ON public.product_purchases FOR SELECT
USING (EXISTS (
  SELECT 1 FROM mentor_products
  JOIN mentor_profiles ON mentor_profiles.id = mentor_products.mentor_id
  WHERE mentor_products.id = product_purchases.product_id
  AND mentor_profiles.user_id = auth.uid()
));

CREATE POLICY "Authenticated users can create purchases"
ON public.product_purchases FOR INSERT
WITH CHECK (auth.uid() = buyer_id);

-- Create storage buckets for product files and previews
INSERT INTO storage.buckets (id, name, public) VALUES ('product-files', 'product-files', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('product-previews', 'product-previews', true);

-- Storage policies for product files (private - only purchasers can access)
CREATE POLICY "Mentors can upload product files"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'product-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Mentors can update their product files"
ON storage.objects FOR UPDATE
USING (bucket_id = 'product-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Mentors can delete their product files"
ON storage.objects FOR DELETE
USING (bucket_id = 'product-files' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Storage policies for product previews (public)
CREATE POLICY "Mentors can upload product previews"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'product-previews' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Anyone can view product previews"
ON storage.objects FOR SELECT
USING (bucket_id = 'product-previews');

CREATE POLICY "Mentors can update their product previews"
ON storage.objects FOR UPDATE
USING (bucket_id = 'product-previews' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Mentors can delete their product previews"
ON storage.objects FOR DELETE
USING (bucket_id = 'product-previews' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Add username field to mentor_profiles for shop URLs
ALTER TABLE public.mentor_profiles ADD COLUMN IF NOT EXISTS username TEXT UNIQUE;

-- Trigger for updating updated_at
CREATE TRIGGER update_mentor_products_updated_at
BEFORE UPDATE ON public.mentor_products
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();