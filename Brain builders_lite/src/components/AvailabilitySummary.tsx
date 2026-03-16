import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { Calendar, Clock, CheckCircle2 } from "lucide-react";

interface AvailabilitySummaryProps {
  mentorId: string;
}

interface WeeklySlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

const DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const SHORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export const AvailabilitySummary = ({ mentorId }: AvailabilitySummaryProps) => {
  const [weeklySlots, setWeeklySlots] = useState<WeeklySlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAvailability();
  }, [mentorId]);

  const loadAvailability = async () => {
    try {
      const { data, error } = await (supabase
        .from("mentor_weekly_availability" as any)
        .select("day_of_week, start_time, end_time")
        .eq("mentor_id", mentorId)
        .eq("is_active", true)
        .order("day_of_week")
        .order("start_time") as any);

      if (error) throw error;
      setWeeklySlots((data as WeeklySlot[]) || []);
    } catch (error) {
      console.error("Error loading availability:", error);
    } finally {
      setLoading(false);
    }
  };

  const groupedByDay = useMemo(() => {
    const grouped: Record<number, WeeklySlot[]> = {};
    weeklySlots.forEach(slot => {
      if (!grouped[slot.day_of_week]) {
        grouped[slot.day_of_week] = [];
      }
      grouped[slot.day_of_week].push(slot);
    });
    return grouped;
  }, [weeklySlots]);

  const formatTime = (time: string) => {
    const [hours] = time.split(":");
    const hour = parseInt(hours);
    const period = hour >= 12 ? "PM" : "AM";
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}${period}`;
  };

  const totalHoursPerWeek = useMemo(() => {
    return weeklySlots.reduce((total, slot) => {
      const start = parseInt(slot.start_time.split(":")[0]);
      const end = parseInt(slot.end_time.split(":")[0]);
      return total + (end - start);
    }, 0);
  }, [weeklySlots]);

  const activeDays = useMemo(() => {
    return Object.keys(groupedByDay).length;
  }, [groupedByDay]);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (weeklySlots.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <p className="text-muted-foreground">No weekly availability set</p>
          <p className="text-sm text-muted-foreground mt-1">
            Set your recurring schedule to start accepting bookings
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6 pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Availability Overview
        </CardTitle>
        <CardDescription>
          Your weekly recurring schedule
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-2">
        {/* Stats row */}
        <div className="flex gap-4 mb-4 pb-4 border-b">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              <strong>{totalHoursPerWeek}</strong> hours/week
            </span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              <strong>{activeDays}</strong> active days
            </span>
          </div>
        </div>

        {/* Visual week grid */}
        <div className="grid grid-cols-7 gap-1 mb-4">
          {DAYS_OF_WEEK.map((day, index) => (
            <div
              key={index}
              className={`text-center p-2 rounded-md ${
                groupedByDay[index]
                  ? "bg-primary/10 text-primary"
                  : "bg-muted/50 text-muted-foreground"
              }`}
            >
              <span className="text-xs font-medium">{SHORT_DAYS[index]}</span>
            </div>
          ))}
        </div>

        {/* Detailed schedule */}
        <div className="space-y-2">
          {DAYS_OF_WEEK.map((day, index) => {
            const slots = groupedByDay[index];
            if (!slots) return null;

            return (
              <div key={index} className="flex items-center gap-3 text-sm">
                <span className="font-medium w-20 text-muted-foreground">{day}</span>
                <div className="flex flex-wrap gap-1">
                  {slots.map((slot, slotIndex) => (
                    <Badge key={slotIndex} variant="outline" className="text-xs">
                      {formatTime(slot.start_time)} - {formatTime(slot.end_time)}
                    </Badge>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default AvailabilitySummary;
