import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar as CalendarIcon, Clock, User, AlertCircle, Download, Mail, DollarSign, XCircle, CheckCircle } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface BookingCalendarProps {
  userId: string;
  userType: "mentor" | "learner";
}

interface CalendarBooking {
  id: string;
  booking_date: string;
  booking_time: string;
  status: string;
  price: string;
  mentor_name?: string;
  user_email?: string;
  learner_name?: string;
  mentor_id: string;
  user_id: string;
}

interface BookingDetails extends CalendarBooking {
  mentor_email?: string;
  mentor_profile_picture?: string;
  learner_profile_picture?: string;
  meeting_link?: string;
  notes?: string;
}

export const BookingCalendarView = ({ userId, userType }: BookingCalendarProps) => {
  const [bookings, setBookings] = useState<CalendarBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedBooking, setSelectedBooking] = useState<BookingDetails | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadBookings();
  }, [userId, userType, selectedDate]);

  const loadBookings = async () => {
    try {
      setLoading(true);

      // Get bookings for the current month
      const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
      const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);

      let query = supabase
        .from("bookings")
        .select("*")
        .gte("booking_date", startOfMonth.toISOString().split("T")[0])
        .lte("booking_date", endOfMonth.toISOString().split("T")[0])
        .in("status", ["confirmed", "pending"]);

      if (userType === "mentor") {
        query = query.eq("mentor_id", userId);
      } else {
        query = query.eq("user_id", userId);
      }

      const { data, error } = await query.order("booking_date").order("booking_time");

      if (error) throw error;

      // Fetch mentor and learner details separately
      if (data && data.length > 0) {
        const mentorIds = [...new Set(data.map((b: any) => b.mentor_id))];
        const userIds = [...new Set(data.map((b: any) => b.user_id))];

        // Get mentor profiles
        const { data: mentors } = await supabase
          .from("mentor_profiles")
          .select("id, name, image_url")
          .in("id", mentorIds);

        // Get learner profiles
        const { data: learners } = await supabase
          .from("profiles")
          .select("id, full_name")
          .in("id", userIds);

        // Transform data to include full names
        const transformedData = data.map((booking: any) => {
          const mentor = mentors?.find((m: any) => m.id === booking.mentor_id);
          const learner = learners?.find((l: any) => l.id === booking.user_id);
          
          return {
            ...booking,
            mentor_name: mentor?.name || booking.mentor_name || "Mentor",
            learner_name: learner?.full_name || booking.user_email?.split('@')[0] || "Learner",
            mentor_profile_picture: mentor?.image_url,
            learner_profile_picture: null, // profiles table doesn't have profile picture
            mentor_email: booking.user_email, // This will be populated from booking
          };
        });

        setBookings(transformedData);
      } else {
        setBookings([]);
      }
    } catch (error: any) {
      console.error("Error loading bookings:", error);
      toast({
        title: "Error",
        description: "Failed to load bookings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = () => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add all days in the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  };

  const getBookingsForDate = (date: Date | null) => {
    if (!date) return [];
    const dateStr = date.toISOString().split("T")[0];
    return bookings.filter((b) => b.booking_date === dateStr);
  };

  const changeMonth = (offset: number) => {
    setSelectedDate(
      new Date(selectedDate.getFullYear(), selectedDate.getMonth() + offset, 1)
    );
  };

  const isToday = (date: Date | null) => {
    if (!date) return false;
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const handleBookingClick = (booking: CalendarBooking) => {
    setSelectedBooking(booking as BookingDetails);
    setDialogOpen(true);
  };

  const generateICSFile = (booking: BookingDetails) => {
    const [hours, minutes] = booking.booking_time.split(':');
    const start = new Date(`${booking.booking_date}T${hours}:${minutes}:00`);
    const end = new Date(start.getTime() + 60 * 60 * 1000); // 60 minutes

    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const otherPersonName = userType === "mentor" 
      ? booking.learner_name 
      : booking.mentor_name;

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Brain Bulders//Booking//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:${booking.id}@g-creators.com
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(start)}
DTEND:${formatDate(end)}
SUMMARY:Mentorship Session with ${otherPersonName}
DESCRIPTION:Your scheduled mentorship session with ${otherPersonName}\\n\\nBooking ID: ${booking.id}\\nPrice: $${parseFloat(booking.price)}
LOCATION:Online Meeting
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:Session with ${otherPersonName} tomorrow
END:VALARM
BEGIN:VALARM
TRIGGER:-PT1H
ACTION:DISPLAY
DESCRIPTION:Session with ${otherPersonName} starting in 1 hour
END:VALARM
END:VEVENT
END:VCALENDAR`;

    return icsContent;
  };

  const downloadICSFile = (booking: BookingDetails) => {
    const icsContent = generateICSFile(booking);
    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `session-${booking.booking_date}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    toast({
      title: "Calendar file downloaded",
      description: "Open the file to add this session to your calendar",
    });
  };

    const handleCancelBooking = async () => {
    if (!selectedBooking) return;
    setActionLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke("cancel-booking", {
        body: { bookingId: selectedBooking.id },
      });
      if (error) throw error;
      if (data?.error) throw new Error(data.error);
      toast({ title: "Session cancelled", description: "The booking has been cancelled." });
      setDialogOpen(false);
      loadBookings();
    } catch (e: unknown) {
      toast({
        title: "Error",
        description: e instanceof Error ? e.message : "Failed to cancel booking",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkCompleted = async () => {
    if (!selectedBooking) return;
    setActionLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke("update-booking-status", {
        body: { bookingId: selectedBooking.id, status: "completed" },
      });
      if (error) throw error;
      if (data?.error) throw new Error(data.error);
      toast({ title: "Session marked as completed" });
      setDialogOpen(false);
      loadBookings();
    } catch (e: unknown) {
      toast({
        title: "Error",
        description: e instanceof Error ? e.message : "Failed to update status",
        variant: "destructive",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const addToGoogleCalendar = (booking: BookingDetails) => {
    const otherPersonName = userType === "mentor" 
      ? booking.learner_name 
      : booking.mentor_name;

    const [hours, minutes] = booking.booking_time.split(':');
    const start = new Date(`${booking.booking_date}T${hours}:${minutes}:00`);
    const end = new Date(start.getTime() + 60 * 60 * 1000);

    // Format dates for Google Calendar (YYYYMMDDTHHMMSSZ)
    const formatGoogleDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const googleCalendarUrl = new URL('https://calendar.google.com/calendar/render');
    googleCalendarUrl.searchParams.set('action', 'TEMPLATE');
    googleCalendarUrl.searchParams.set('text', `Mentorship Session with ${otherPersonName}`);
    googleCalendarUrl.searchParams.set('details', `Your scheduled mentorship session\n\nPrice: $${parseFloat(booking.price)}`);
    googleCalendarUrl.searchParams.set('dates', `${formatGoogleDate(start)}/${formatGoogleDate(end)}`);
    googleCalendarUrl.searchParams.set('location', 'Online Meeting');

    window.open(googleCalendarUrl.toString(), '_blank');

    toast({
      title: "Opening Google Calendar",
      description: "Add this session to your Google Calendar",
    });
  };

  const days = getDaysInMonth();
  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarIcon className="h-5 w-5" />
          My Calendar
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => changeMonth(-1)}
            className="px-3 py-1 text-sm hover:bg-muted rounded"
          >
            ← Prev
          </button>
          <h3 className="font-semibold">
            {selectedDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </h3>
          <button
            onClick={() => changeMonth(1)}
            className="px-3 py-1 text-sm hover:bg-muted rounded"
          >
            Next →
          </button>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1 mb-4">
          {weekDays.map((day) => (
            <div key={day} className="text-center text-xs font-medium text-muted-foreground p-2">
              {day}
            </div>
          ))}
          {days.map((date, index) => {
            const dayBookings = getBookingsForDate(date);
            const hasBookings = dayBookings.length > 0;

            return (
              <div
                key={index}
                className={`
                  min-h-[60px] p-1 border rounded text-sm
                  ${!date ? "bg-muted/20" : "bg-background"}
                  ${isToday(date) ? "border-primary border-2" : "border-border"}
                  ${hasBookings ? "bg-blue-50 dark:bg-blue-950 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900" : ""}
                `}
              >
                {date && (
                  <>
                    <div className={`text-right ${isToday(date) ? "font-bold text-primary" : ""}`}>
                      {date.getDate()}
                    </div>
                    {dayBookings.map((booking) => (
                      <div
                        key={booking.id}
                        onClick={() => handleBookingClick(booking)}
                        className="mt-1 px-1 py-0.5 text-[10px] bg-primary/20 hover:bg-primary/30 rounded truncate cursor-pointer transition-colors"
                        title={`${booking.booking_time} - ${userType === "mentor" ? booking.learner_name : booking.mentor_name}`}
                      >
                        {booking.booking_time?.substring(0, 5)}
                      </div>
                    ))}
                  </>
                )}
              </div>
            );
          })}
        </div>

        {/* Upcoming Bookings List — only shown for learners; mentors have a dedicated card below */}
        {userType === "learner" && (
          <div className="space-y-2 mt-4">
            <h4 className="font-semibold text-sm">Upcoming Sessions</h4>
            {bookings.slice(0, 5).map((booking) => (
              <div
                key={booking.id}
                onClick={() => handleBookingClick(booking)}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">
                      {new Date(booking.booking_date + "T00:00:00").toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {booking.booking_time}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs font-medium">{booking.mentor_name}</p>
                  <Badge variant={booking.status === "confirmed" ? "default" : "secondary"}>
                    {booking.status}
                  </Badge>
                </div>
              </div>
            ))}
            {bookings.length === 0 && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>No upcoming sessions scheduled</AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </CardContent>

      {/* Booking Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Session Details</DialogTitle>
            <DialogDescription>
              Your scheduled mentorship session
            </DialogDescription>
          </DialogHeader>
          
          {selectedBooking && (
            <div className="space-y-4">
              {/* Date & Time */}
              <div className="flex items-center gap-3 p-4 bg-primary/5 rounded-lg border border-primary/20">
                <CalendarIcon className="h-5 w-5 text-primary flex-shrink-0" />
                <div className="flex-1">
                  <p className="font-semibold text-base">
                    {new Date(selectedBooking.booking_date + "T00:00:00").toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1.5 mt-1">
                    <Clock className="h-3.5 w-3.5" />
                    {selectedBooking.booking_time.substring(0, 5)} • 60 minutes
                  </p>
                </div>
              </div>

              {/* Participant Info */}
              <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg">
                <User className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                    {userType === "mentor" ? "Learner" : "Mentor"}
                  </p>
                  <p className="font-semibold text-base truncate">
                    {userType === "mentor" ? selectedBooking.learner_name : selectedBooking.mentor_name}
                  </p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1.5 mt-1 truncate">
                    <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="truncate">
                      {userType === "mentor" ? selectedBooking.user_email : selectedBooking.mentor_email}
                    </span>
                  </p>
                </div>
              </div>

              {/* Price & Status */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                    Price
                  </p>
                  <p className="font-bold text-xl flex items-center gap-1">
                    <DollarSign className="h-5 w-5" />
                    {parseFloat(selectedBooking.price).toFixed(2)}
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                    Status
                  </p>
                  <Badge 
                    variant={selectedBooking.status === "confirmed" ? "default" : "secondary"}
                    className="text-sm px-3 py-1"
                  >
                    {selectedBooking.status}
                  </Badge>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-2 pt-2">
                <Button
                  onClick={() => addToGoogleCalendar(selectedBooking)}
                  variant="default"
                  className="w-full"
                  size="lg"
                >
                  <CalendarIcon className="h-4 w-4 mr-2" />
                  Add to Google Calendar
                </Button>
                <Button
                  onClick={() => downloadICSFile(selectedBooking)}
                  variant="outline"
                  className="w-full"
                  size="lg"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download ICS File
                </Button>

                {/* Cancel & Mark completed (role-based) */}
                <div className="flex gap-2 pt-2 border-t">
                  <Button
                    onClick={handleCancelBooking}
                    variant="outline"
                    className="flex-1"
                    size="lg"
                    disabled={actionLoading}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Cancel Session
                  </Button>
                  {userType === "mentor" && (
                    <Button
                      onClick={handleMarkCompleted}
                      variant="default"
                      className="flex-1"
                      size="lg"
                      disabled={actionLoading}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Mark Completed
                    </Button>
                  )}
                </div>
              </div>

              <p className="text-xs text-center text-muted-foreground px-2">
                Use Google Calendar for quick add, or download ICS for Outlook, Apple Calendar, and other apps
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
};
