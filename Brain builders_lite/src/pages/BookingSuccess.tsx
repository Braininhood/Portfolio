import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle2, Download, ArrowLeft, ExternalLink } from "lucide-react";
import { getGoogleCalendarUrl } from "@/utils/calendar";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const BookingSuccess = () => {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const [bookingDetails, setBookingDetails] = useState<any>(null);
  const [calendarEvent, setCalendarEvent] = useState<string | null>(null);

  // Get params from URL
  const searchParams = new URLSearchParams(window.location.search);
  const sessionId = searchParams.get("session_id");
  const bookingId = searchParams.get("booking_id");

  // Process the booking confirmation once when we have session_id and booking_id
  useEffect(() => {
    if (!sessionId || !bookingId || bookingDetails) return;

    let cancelled = false;

    const processBooking = async () => {
      setIsProcessing(true);
      try {
        const { data, error } = await supabase.functions.invoke("send-booking-confirmation", {
          body: { sessionId, bookingId },
        });

        if (cancelled) return;
        if (error) throw error;

        setBookingDetails(data?.booking ?? null);
        setCalendarEvent(data?.calendarEvent ?? null);
        toast.success("Booking confirmed!", {
          description: "A confirmation email has been sent to you.",
        });
      } catch (error) {
        if (cancelled) return;
        console.error("Error confirming booking:", error);
        toast.error("Error confirming booking", {
          description: "Please contact support if payment was processed.",
        });
      } finally {
        if (!cancelled) setIsProcessing(false);
      }
    };

    processBooking();
    return () => { cancelled = true; };
  }, [sessionId, bookingId]);

  const downloadCalendarEvent = () => {
    if (!calendarEvent) return;

    const blob = new Blob([calendarEvent], { type: "text/calendar" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mentorship-session.ics";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success("Calendar event downloaded!");
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-32 pb-16">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto">
            <Card className="border-2 border-accent/20">
              <CardContent className="p-12">
                <div className="text-center space-y-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 mb-4">
                    <CheckCircle2 className="text-green-600" size={48} />
                  </div>

                  <div>
                    <h1 className="text-4xl font-display font-bold mb-2">
                      Payment Successful!
                    </h1>
                    <p className="text-xl text-muted-foreground">
                      Your mentorship session has been confirmed
                    </p>
                  </div>

                  {isProcessing && (
                    <div className="py-8">
                      <div className="animate-pulse space-y-4">
                        <div className="h-4 bg-muted rounded w-3/4 mx-auto" />
                        <div className="h-4 bg-muted rounded w-1/2 mx-auto" />
                      </div>
                      <p className="text-sm text-muted-foreground mt-4">
                        Processing your booking...
                      </p>
                    </div>
                  )}

                  {bookingDetails && (
                    <Card className="bg-gradient-accent">
                      <CardContent className="p-6 text-left space-y-4">
                        <h2 className="text-xl font-display font-bold mb-4">
                          Session Details
                        </h2>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Mentor:</span>
                            <span className="font-semibold">{bookingDetails.mentor_name}</span>
                          </div>
                          
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Date:</span>
                            <span className="font-semibold">
                              {formatDate(bookingDetails.booking_date)}
                            </span>
                          </div>
                          
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Time:</span>
                            <span className="font-semibold">{bookingDetails.booking_time}</span>
                          </div>
                          
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Duration:</span>
                            <span className="font-semibold">60 minutes</span>
                          </div>
                          
                          <div className="flex justify-between pt-2 border-t border-border">
                            <span className="text-muted-foreground">Amount Paid:</span>
                            <span className="font-bold text-lg">
                              ${parseFloat(bookingDetails.price).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <div className="space-y-3 pt-4">
                    {bookingDetails && (
                      <>
                        <Button
                          variant="hero"
                          size="lg"
                          className="w-full"
                          onClick={() => {
                            const url = getGoogleCalendarUrl({
                              title: `Session with ${bookingDetails.mentor_name}`,
                              startDate: bookingDetails.booking_date,
                              startTime: bookingDetails.booking_time,
                              durationMinutes: 60,
                            });
                            window.open(url, "_blank");
                          }}
                        >
                          <ExternalLink size={20} className="mr-2" />
                          Add to Google Calendar
                        </Button>
                        {calendarEvent && (
                          <Button
                            variant="outline"
                            size="lg"
                            className="w-full"
                            onClick={downloadCalendarEvent}
                          >
                            <Download size={20} className="mr-2" />
                            Download ICS file
                          </Button>
                        )}
                      </>
                    )}

                    <Button
                      variant="outline"
                      size="lg"
                      className="w-full"
                      onClick={() => navigate("/mentors")}
                    >
                      <ArrowLeft size={20} className="mr-2" />
                      Back to Mentors
                    </Button>
                  </div>

                  <div className="pt-6 border-t border-border">
                    <p className="text-sm text-muted-foreground">
                      A confirmation email has been sent to <strong>{bookingDetails?.user_email}</strong>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default BookingSuccess;