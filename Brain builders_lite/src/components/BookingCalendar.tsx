import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Calendar, Clock, Loader2, Video } from "lucide-react";
import TimeSlotSelector from "./TimeSlotSelector";

interface TimeSlot {
  id: string;
  mentor_id: string;
  date: string;
  time: string;
  is_available: boolean;
  mentor_profiles: {
    name: string;
    price: number;
  };
}

interface BookingCalendarProps {
  mentorId: string;
  mentorName: string;
  mentorPrice: number;
  timeSlots: TimeSlot[];
  onBookingComplete?: () => void;
}

export const BookingCalendar = ({
  mentorId,
  mentorName,
  mentorPrice,
  timeSlots,
  onBookingComplete,
}: BookingCalendarProps) => {
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [topic, setTopic] = useState("");
  const [meetingPlatform, setMeetingPlatform] = useState("zoom");
  const [isBooking, setIsBooking] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSlotSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot);
  };

  const handleBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedSlot) {
      toast({
        title: "No Time Slot Selected",
        description: "Please select a time slot first",
        variant: "destructive",
      });
      return;
    }

    if (!name || !email || !topic) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    setIsBooking(true);

    try {
      const { data: { session: authSession }, error: refreshErr } = await supabase.auth.refreshSession();
      if (refreshErr || !authSession?.access_token) {
        setIsBooking(false);
        toast({
          title: "Authentication Required",
          description: "Please sign in to book a session.",
          variant: "destructive",
        });
        navigate("/auth");
        return;
      }

      const { data, error } = await supabase.functions.invoke("create-booking", {
        body: {
          mentorId,
          mentorName,
          bookingDate: selectedSlot.date,
          bookingTime: selectedSlot.time,
          price: mentorPrice,
          timeSlotId: selectedSlot.id,
          meetingPlatform,
          notes: `Topic: ${topic}\nName: ${name}`,
        },
        headers: { Authorization: `Bearer ${authSession.access_token}` },
      });

      if (error) {
        const status = (error as { context?: { status?: number } })?.context?.status;
        if (status === 401) {
          setIsBooking(false);
          toast({
            title: "Session expired or invalid",
            description: "Please sign in again.",
            variant: "destructive",
          });
          navigate("/auth");
          return;
        }
        throw error;
      }

      // Redirect to Stripe Checkout
      if (data?.sessionUrl) {
        onBookingComplete?.();
        window.location.href = data.sessionUrl;
      } else {
        throw new Error("No checkout URL returned");
      }
    } catch (error) {
      console.error("Error creating booking:", error);
      toast({
        title: "Booking Failed",
        description: "Failed to create booking. Please try again.",
        variant: "destructive",
      });
      setIsBooking(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Select a Time Slot
          </CardTitle>
          <CardDescription>
            Book a 1-hour consultation session with {mentorName}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TimeSlotSelector
            timeSlots={timeSlots}
            onSelectSlot={handleSlotSelect}
          />
        </CardContent>
      </Card>

      {selectedSlot && (
        <Card>
          <CardHeader>
            <CardTitle>Booking Details</CardTitle>
            <CardDescription>
              Complete your booking for {selectedSlot.date} at {selectedSlot.time}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBooking} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name *</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Your name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="topic">Session Topic *</Label>
                <Textarea
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="What would you like to discuss?"
                  rows={3}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="platform">Meeting Platform</Label>
                <Select value={meetingPlatform} onValueChange={setMeetingPlatform}>
                  <SelectTrigger id="platform">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="zoom">
                      <div className="flex items-center gap-2">
                        <Video className="h-4 w-4" />
                        Zoom
                      </div>
                    </SelectItem>
                    <SelectItem value="google-meet">
                      <div className="flex items-center gap-2">
                        <Video className="h-4 w-4" />
                        Google Meet
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">Total Price</p>
                  <p className="text-2xl font-bold">${mentorPrice}/hour</p>
                </div>
                <Button type="submit" disabled={isBooking} size="lg">
                  {isBooking ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Clock className="mr-2 h-4 w-4" />
                      Confirm Booking
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
