-- Create product reviews table
CREATE TABLE public.product_reviews (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  product_id UUID NOT NULL REFERENCES public.mentor_products(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  user_name TEXT NOT NULL,
  user_avatar TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(product_id, user_id)
);

-- Enable RLS
ALTER TABLE public.product_reviews ENABLE ROW LEVEL SECURITY;

-- Anyone can view reviews
CREATE POLICY "Anyone can view product reviews"
ON public.product_reviews
FOR SELECT
USING (true);

-- Only buyers who purchased can create reviews
CREATE POLICY "Buyers can create reviews for purchased products"
ON public.product_reviews
FOR INSERT
WITH CHECK (
  auth.uid() = user_id AND
  EXISTS (
    SELECT 1 FROM public.product_purchases
    WHERE product_purchases.product_id = product_reviews.product_id
    AND product_purchases.buyer_id = auth.uid()
    AND product_purchases.status = 'completed'
  )
);

-- Users can update their own reviews
CREATE POLICY "Users can update their own reviews"
ON public.product_reviews
FOR UPDATE
USING (auth.uid() = user_id);

-- Users can delete their own reviews
CREATE POLICY "Users can delete their own reviews"
ON public.product_reviews
FOR DELETE
USING (auth.uid() = user_id);

-- Add rating columns to mentor_products
ALTER TABLE public.mentor_products
ADD COLUMN IF NOT EXISTS average_rating NUMERIC DEFAULT 0,
ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;

-- Create function to update product rating
CREATE OR REPLACE FUNCTION public.update_product_rating()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    UPDATE public.mentor_products
    SET 
      average_rating = COALESCE((
        SELECT AVG(rating)::NUMERIC(3,2)
        FROM public.product_reviews
        WHERE product_id = OLD.product_id
      ), 0),
      review_count = (
        SELECT COUNT(*)
        FROM public.product_reviews
        WHERE product_id = OLD.product_id
      ),
      updated_at = now()
    WHERE id = OLD.product_id;
    RETURN OLD;
  ELSE
    UPDATE public.mentor_products
    SET 
      average_rating = COALESCE((
        SELECT AVG(rating)::NUMERIC(3,2)
        FROM public.product_reviews
        WHERE product_id = NEW.product_id
      ), 0),
      review_count = (
        SELECT COUNT(*)
        FROM public.product_reviews
        WHERE product_id = NEW.product_id
      ),
      updated_at = now()
    WHERE id = NEW.product_id;
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Create trigger
CREATE TRIGGER update_product_rating_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.product_reviews
FOR EACH ROW
EXECUTE FUNCTION public.update_product_rating();