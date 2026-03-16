-- Allow admins to fully manage (insert, update, delete) for admin panel

-- Bookings
CREATE POLICY "Admins can insert bookings"
  ON public.bookings FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update bookings"
  ON public.bookings FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete bookings"
  ON public.bookings FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

-- Profiles (learners / users)
CREATE POLICY "Admins can update profiles"
  ON public.profiles FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

-- Mentor questions (admin can update status, delete, insert for "ask admin" flow)
CREATE POLICY "Admins can insert mentor_questions"
  ON public.mentor_questions FOR INSERT
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update mentor_questions"
  ON public.mentor_questions FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete mentor_questions"
  ON public.mentor_questions FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

-- Product purchases (admin can update status)
CREATE POLICY "Admins can update product_purchases"
  ON public.product_purchases FOR UPDATE
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete product_purchases"
  ON public.product_purchases FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));

-- Push subscriptions (admin can delete)
CREATE POLICY "Admins can delete push_subscriptions"
  ON public.push_subscriptions FOR DELETE
  USING (public.has_role(auth.uid(), 'admin'));
