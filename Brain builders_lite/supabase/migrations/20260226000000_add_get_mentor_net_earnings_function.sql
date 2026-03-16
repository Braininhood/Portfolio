-- Helper function to get mentor's net earnings from transactions
CREATE OR REPLACE FUNCTION public.get_mentor_net_earnings(mentor_profile_id UUID)
RETURNS DECIMAL(10,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  total_net DECIMAL(10,2);
BEGIN
  SELECT COALESCE(SUM(net_amount), 0)
  INTO total_net
  FROM public.transactions
  WHERE mentor_id = mentor_profile_id
    AND status = 'completed';
  
  RETURN total_net;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.get_mentor_net_earnings(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_mentor_net_earnings(UUID) TO anon;
