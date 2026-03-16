import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Loader2, CheckCircle } from "lucide-react";

export interface MentorBooking {
  id: string;
  mentor_id: string;
  user_email: string;
  booking_date: string;
  booking_time: string;
  status: string;
  price: number;
  meeting_link: string | null;
  meeting_platform: string | null;
  notes: string | null;
}

/** Normalize time to HH:mm or HH:mm:ss for consistent comparison (DB may return 15:00:00, booking may be 15:00). */
function normalizeTime(t: string): string {
  if (!t) return t;
  const parts = t.trim().split(":");
  if (parts.length >= 2) return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}`;
  return t;
}

interface TimeSlotOption {
  id: string;
  date: string;
  time: string;
  is_available: boolean | null;
  booking_id?: string | null;
}

/** Normalize date to YYYY-MM-DD for comparison (DB may return with time or timezone). */
function normalizeDate(d: string): string {
  if (!d) return d;
  return d.split("T")[0];
}
/** Booked key for set lookup: normalize so "15:00" and "15:00:00" match */
function bookedKey(date: string, time: string): string {
  return `${normalizeDate(date)}_${normalizeTime(time)}`;
}

interface WeeklySlotRow {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

/** Generate 1-hour slots from weekly availability for the next 4 weeks (same as MentorProfile booking page). */
function generateSlotsFromWeekly(mentorId: string, weeklySlots: WeeklySlotRow[]): TimeSlotOption[] {
  const slots: TimeSlotOption[] = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  for (let dayOffset = 0; dayOffset < 28; dayOffset++) {
    const date = new Date(today);
    date.setDate(today.getDate() + dayOffset);
    const dayOfWeek = date.getDay();
    const daySlots = weeklySlots.filter((s) => s.day_of_week === dayOfWeek);
    daySlots.forEach((slot) => {
      const startHour = parseInt(slot.start_time.split(":")[0], 10);
      const endHour = parseInt(slot.end_time.split(":")[0], 10);
      for (let hour = startHour; hour < endHour; hour++) {
        const timeStr = `${hour.toString().padStart(2, "0")}:00:00`;
        const dateStr = date.toISOString().split("T")[0];
        const slotDateTime = new Date(`${dateStr}T${timeStr}`);
        if (slotDateTime <= new Date()) continue;
        slots.push({
          id: `${mentorId}_${dateStr}_${timeStr}`,
          date: dateStr,
          time: timeStr,
          is_available: true,
        });
      }
    });
  }
  return slots.sort((a, b) => {
    const c = a.date.localeCompare(b.date);
    return c !== 0 ? c : a.time.localeCompare(b.time);
  });
}

interface MentorSessionEditDialogProps {
  booking: MentorBooking | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
  onMarkCompleted?: () => void;
}

export function MentorSessionEditDialog({
  booking,
  open,
  onOpenChange,
  onSaved,
  onMarkCompleted,
}: MentorSessionEditDialogProps) {
  const [meetingLink, setMeetingLink] = useState("");
  const [markingCompleted, setMarkingCompleted] = useState(false);
  const [meetingPlatform, setMeetingPlatform] = useState("");
  const [notes, setNotes] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [availableSlots, setAvailableSlots] = useState<TimeSlotOption[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (!booking || !open) return;
    setMeetingLink(booking.meeting_link ?? "");
    setMeetingPlatform(booking.meeting_platform ?? "");
    setNotes(booking.notes ?? "");
    setSelectedDate(booking.booking_date);
    setSelectedTime(booking.booking_time);
  }, [booking, open]);

  useEffect(() => {
    if (!booking?.mentor_id || !open) return;
    setLoadingSlots(true);
    const mentorId = booking.mentor_id;
    const todayStr = new Date().toISOString().split("T")[0];

    (async () => {
      try {
        // Same as mentor profile booking page: weekly availability + bookings for free slots
        const { data: weeklyData } = await supabase
          .from("mentor_weekly_availability")
          .select("day_of_week, start_time, end_time")
          .eq("mentor_id", mentorId)
          .eq("is_active", true);

        if (weeklyData && weeklyData.length > 0) {
          const generated = generateSlotsFromWeekly(mentorId, weeklyData as WeeklySlotRow[]);

          const { data: bookingsData } = await supabase
            .from("bookings")
            .select("id, booking_date, booking_time")
            .eq("mentor_id", mentorId)
            .in("status", ["pending", "confirmed"])
            .gte("booking_date", todayStr);

          const bookedKeys = new Set<string>();
          (bookingsData || []).forEach((b) => {
            if (b.id === booking.id) return;
            bookedKeys.add(bookedKey(b.booking_date, b.booking_time));
          });

          const slotsWithAvailability = generated.map((s) => ({
            ...s,
            is_available: !bookedKeys.has(bookedKey(s.date, s.time)),
          }));
          setAvailableSlots(slotsWithAvailability);
        } else {
          // Fallback: mentor_time_slots (e.g. no weekly availability)
          const { data } = await supabase
            .from("mentor_time_slots")
            .select("id, date, time, is_available, booking_id")
            .eq("mentor_id", mentorId)
            .gte("date", todayStr)
            .order("date")
            .order("time");
          setAvailableSlots((data as TimeSlotOption[]) ?? []);
        }
      } finally {
        setLoadingSlots(false);
      }
    })();
  }, [booking?.mentor_id, booking?.id, open]);

  if (!booking) return null;

  const normBookingDate = normalizeDate(booking.booking_date);
  const dateTimeChanged =
    normalizeDate(selectedDate) !== normBookingDate || normalizeTime(selectedTime) !== normalizeTime(booking.booking_time);
  const normBookingTime = normalizeTime(booking.booking_time);
  // Selectable: available slots (from weekly+bookings) or current booking slot (by booking_id or date+time for fallback)
  const availableForSelect = availableSlots.filter(
    (s) =>
      s.is_available === true ||
      s.booking_id === booking.id ||
      (normalizeDate(s.date) === normBookingDate && normalizeTime(s.time) === normBookingTime)
  );
  const isDbSlotId = (id: string) => /^[0-9a-f-]{36}$/i.test(id);
  // Always include current booking date/time in options so dropdowns show existing values
  const dateSet = new Set(availableForSelect.map((s) => normalizeDate(s.date)));
  if (normBookingDate && !dateSet.has(normBookingDate)) dateSet.add(normBookingDate);
  const uniqueDates = [...dateSet].sort();
  const baseTimes = selectedDate
    ? availableForSelect
        .filter((s) => normalizeDate(s.date) === normalizeDate(selectedDate))
        .map((s) => s.time)
    : [];
  const timeSet = new Set(baseTimes);
  const bookingTimeForList = booking.booking_time.trim();
  if (
    normalizeDate(selectedDate) === normBookingDate &&
    bookingTimeForList &&
    !baseTimes.some((t) => normalizeTime(t) === normBookingTime)
  ) {
    timeSet.add(bookingTimeForList);
  }
  const timesForDate = [...timeSet].sort();
  // Resolve date for Select: value must match an option (use normalized form)
  const resolvedDate =
    selectedDate && !uniqueDates.includes(selectedDate) && uniqueDates.some((d) => normalizeDate(d) === normalizeDate(selectedDate))
      ? uniqueDates.find((d) => normalizeDate(d) === normalizeDate(selectedDate)) ?? selectedDate
      : selectedDate;
  // Normalize selected time for display: if current value isn't in list but matches a list item when normalized, use the list item so Select shows it
  const resolvedTime =
    selectedTime && !timesForDate.includes(selectedTime) && timesForDate.some((t) => normalizeTime(t) === normalizeTime(selectedTime))
      ? timesForDate.find((t) => normalizeTime(t) === normalizeTime(selectedTime)) ?? selectedTime
      : selectedTime;

  const handleSave = async () => {
    if (!booking) return;
    setSaving(true);
    try {
      const newDate = selectedDate;
      const newTime = selectedTime;
      const dateTimeChanged = newDate !== booking.booking_date || newTime !== booking.booking_time;

      let finalDate = newDate;
      let finalTime = newTime;
      if (dateTimeChanged) {
        const newSlot = availableForSelect.find(
          (s) => normalizeDate(s.date) === normalizeDate(newDate) && normalizeTime(s.time) === normalizeTime(newTime)
        );
        if (newSlot) {
          finalDate = newSlot.date;
          finalTime = newSlot.time;
        }
        // Only update mentor_time_slots when we have DB slot rows (fallback path); generated slots use composite ids
        if (newSlot && isDbSlotId(newSlot.id)) {
          const oldSlots = await supabase
            .from("mentor_time_slots")
            .select("id")
            .eq("booking_id", booking.id);
          for (const row of oldSlots.data ?? []) {
            await supabase
              .from("mentor_time_slots")
              .update({ booking_id: null, is_available: true })
              .eq("id", row.id);
          }
          await supabase
            .from("mentor_time_slots")
            .update({ booking_id: booking.id, is_available: false })
            .eq("id", newSlot.id);
        }
      }

      const { error } = await supabase
        .from("bookings")
        .update({
          meeting_link: meetingLink.trim() || null,
          meeting_platform: meetingPlatform.trim() || null,
          notes: notes.trim() || null,
          ...(dateTimeChanged && {
            booking_date: finalDate,
            booking_time: finalTime,
          }),
        })
        .eq("id", booking.id);

      if (error) throw error;
      toast({ title: "Session updated" });
      onOpenChange(false);
      onSaved();
    } catch (e: unknown) {
      toast({
        title: "Error",
        description: e instanceof Error ? e.message : "Failed to update session",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit session</DialogTitle>
          <DialogDescription className="sr-only">
            Change meeting link, platform, notes, or date and time from your availability.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Meeting link</Label>
            <Input
              value={meetingLink}
              onChange={(e) => setMeetingLink(e.target.value)}
              placeholder="https://..."
            />
          </div>
          <div>
            <Label>Meeting platform</Label>
            <Input
              value={meetingPlatform}
              onChange={(e) => setMeetingPlatform(e.target.value)}
              placeholder="Zoom, Google Meet, etc."
            />
          </div>
          <div>
            <Label>Notes</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes"
            />
          </div>
          <div>
            <Label>Date & time (from your availability)</Label>
            {loadingSlots ? (
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading slots…
              </p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Select value={resolvedDate} onValueChange={(v) => { setSelectedDate(v); setSelectedTime(""); }}>
                  <SelectTrigger><SelectValue placeholder="Date" /></SelectTrigger>
                  <SelectContent className="z-[100]">
                    {uniqueDates.map((d) => (
                      <SelectItem key={d} value={d}>
                        {new Date(d).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={resolvedTime} onValueChange={setSelectedTime} disabled={!selectedDate}>
                  <SelectTrigger><SelectValue placeholder="Time" /></SelectTrigger>
                  <SelectContent className="z-[100]">
                    {timesForDate.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {dateTimeChanged && (
              <p className="text-xs text-muted-foreground mt-1">
                Your previous slot will be freed and the new slot will be reserved for this session.
              </p>
            )}
          </div>
          <div className="flex justify-between gap-2 pt-2">
            <div>
              {onMarkCompleted && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={async () => {
                    if (!booking) return;
                    setMarkingCompleted(true);
                    try {
                      const { data, error } = await supabase.functions.invoke("update-booking-status", {
                        body: { bookingId: booking.id, status: "completed" },
                      });
                      if (error) throw error;
                      if (data?.error) throw new Error(data.error);
                      toast({ title: "Session marked as completed" });
                      onOpenChange(false);
                      onMarkCompleted();
                    } catch (e: unknown) {
                      toast({
                        title: "Error",
                        description: e instanceof Error ? e.message : "Failed to update",
                        variant: "destructive",
                      });
                    } finally {
                      setMarkingCompleted(false);
                    }
                  }}
                  disabled={markingCompleted || saving}
                >
                  {markingCompleted ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
                  <span className="ml-2">Mark Completed</span>
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}