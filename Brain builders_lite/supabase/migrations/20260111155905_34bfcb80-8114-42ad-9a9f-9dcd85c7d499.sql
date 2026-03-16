-- Function to generate time slots from weekly availability for a given date range
-- Using non-reserved variable names to avoid syntax errors
CREATE OR REPLACE FUNCTION public.generate_time_slots_from_weekly(
  p_mentor_id UUID,
  p_start_date DATE,
  p_end_date DATE
)
RETURNS TABLE (
  slot_date DATE,
  slot_time TIME,
  day_name TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_current_date DATE := p_start_date;
  v_slot_record RECORD;
  v_current_time TIME;
BEGIN
  -- Loop through each date in the range
  WHILE v_current_date <= p_end_date LOOP
    -- Get weekly availability for this day of week
    FOR v_slot_record IN
      SELECT start_time, end_time
      FROM public.mentor_weekly_availability
      WHERE mentor_id = p_mentor_id
        AND day_of_week = EXTRACT(DOW FROM v_current_date)::INTEGER
        AND is_active = true
    LOOP
      -- Generate 1-hour slots within this time range
      v_current_time := v_slot_record.start_time;
      WHILE v_current_time < v_slot_record.end_time LOOP
        slot_date := v_current_date;
        slot_time := v_current_time;
        day_name := to_char(v_current_date, 'Day');
        RETURN NEXT;
        v_current_time := v_current_time + INTERVAL '1 hour';
      END LOOP;
    END LOOP;
    
    v_current_date := v_current_date + 1;
  END LOOP;
END;
$$;