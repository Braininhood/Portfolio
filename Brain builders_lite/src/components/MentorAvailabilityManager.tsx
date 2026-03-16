import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Calendar, Clock, Plus, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface TimeSlot {
  id: string;
  date: string;
  time: string;
  is_available: boolean;
}

interface MentorAvailabilityManagerProps {
  mentorId: string;
  timeSlots: TimeSlot[];
  onUpdate: () => void;
}

export const MentorAvailabilityManager = ({ mentorId, timeSlots, onUpdate }: MentorAvailabilityManagerProps) => {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const { toast } = useToast();

  const handleAddTimeSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const { error } = await supabase
      .from("mentor_time_slots")
      .insert({
        mentor_id: mentorId,
        date,
        time,
        is_available: true
      });

    if (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Time slot added successfully",
      });
      setDate("");
      setTime("");
      onUpdate();
    }
  };

  const handleDeleteTimeSlot = async (slotId: string) => {
    const { error } = await supabase
      .from("mentor_time_slots")
      .delete()
      .eq("id", slotId);

    if (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } else {
      toast({
        title: "Success",
        description: "Time slot removed",
      });
      onUpdate();
    }
  };

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6">
        <CardTitle className="text-lg sm:text-xl">Availability Management</CardTitle>
        <CardDescription className="text-sm">Manage your available time slots for bookings</CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0 space-y-4 sm:space-y-6">
        <form onSubmit={handleAddTimeSlot} className="space-y-3 sm:space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="date" className="text-xs sm:text-sm">Date</Label>
              <Input
                id="date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>
            <div className="space-y-1.5 sm:space-y-2">
              <Label htmlFor="time" className="text-xs sm:text-sm">Time</Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                required
                className="h-9 sm:h-10 text-sm"
              />
            </div>
            <div className="flex items-end col-span-2 sm:col-span-1">
              <Button type="submit" className="w-full h-9 sm:h-10 text-sm">
                <Plus className="mr-1.5 sm:mr-2 h-4 w-4" />
                Add Slot
              </Button>
            </div>
          </div>
        </form>

        <div className="space-y-3 sm:space-y-4">
          <h3 className="text-xs sm:text-sm font-semibold">Available Time Slots</h3>
          {timeSlots.length === 0 ? (
            <p className="text-xs sm:text-sm text-muted-foreground text-center py-4">
              No time slots configured yet
            </p>
          ) : (
            <div className="grid gap-2">
              {timeSlots.map((slot) => (
                <div 
                  key={slot.id} 
                  className="flex items-center justify-between p-2.5 sm:p-3 border rounded-lg gap-2"
                >
                  <div className="flex flex-wrap items-center gap-2 sm:gap-4 flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm">
                      <Calendar className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground shrink-0" />
                      <span className="truncate">{new Date(slot.date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm">
                      <Clock className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-muted-foreground shrink-0" />
                      <span>{slot.time}</span>
                    </div>
                    <Badge variant={slot.is_available ? "default" : "secondary"} className="text-[10px] sm:text-xs">
                      {slot.is_available ? "Available" : "Booked"}
                    </Badge>
                  </div>
                  {slot.is_available && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteTimeSlot(slot.id)}
                      className="h-8 w-8 p-0 shrink-0"
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
