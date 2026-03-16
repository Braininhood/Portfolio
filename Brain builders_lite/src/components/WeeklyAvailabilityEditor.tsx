import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import { Plus, Trash2, Clock, Copy, Check, Calendar } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface TimeRange {
  id?: string;
  start_time: string;
  end_time: string;
}

interface DayAvailability {
  day: number;
  dayName: string;
  timeRanges: TimeRange[];
}

interface WeeklyAvailabilityEditorProps {
  mentorId: string;
  onUpdate?: () => void;
}

const DAYS_OF_WEEK = [
  { day: 0, name: "Sunday", short: "Sun" },
  { day: 1, name: "Monday", short: "Mon" },
  { day: 2, name: "Tuesday", short: "Tue" },
  { day: 3, name: "Wednesday", short: "Wed" },
  { day: 4, name: "Thursday", short: "Thu" },
  { day: 5, name: "Friday", short: "Fri" },
  { day: 6, name: "Saturday", short: "Sat" },
];

const TIME_OPTIONS = Array.from({ length: 24 }, (_, i) => {
  const hour = i.toString().padStart(2, "0");
  return { value: `${hour}:00:00`, label: `${hour}:00` };
});

export const WeeklyAvailabilityEditor = ({ mentorId, onUpdate }: WeeklyAvailabilityEditorProps) => {
  const [availability, setAvailability] = useState<DayAvailability[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copyFromDay, setCopyFromDay] = useState<number | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadAvailability();
  }, [mentorId]);

  const loadAvailability = async () => {
    setLoading(true);
    
    // Initialize with empty arrays for each day
    const initialAvailability: DayAvailability[] = DAYS_OF_WEEK.map(d => ({
      day: d.day,
      dayName: d.name,
      timeRanges: [],
    }));

    try {
      const { data, error } = await (supabase
        .from("mentor_weekly_availability" as any)
        .select("*")
        .eq("mentor_id", mentorId)
        .eq("is_active", true)
        .order("start_time") as any);

      if (error) throw error;

      // Populate with existing data
      (data as any[])?.forEach((slot) => {
        const dayIndex = initialAvailability.findIndex(d => d.day === slot.day_of_week);
        if (dayIndex !== -1) {
          initialAvailability[dayIndex].timeRanges.push({
            id: slot.id,
            start_time: slot.start_time,
            end_time: slot.end_time,
          });
        }
      });

      setAvailability(initialAvailability);
    } catch (error: any) {
      toast({
        title: "Error loading availability",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const addTimeRange = (dayIndex: number) => {
    const newAvailability = [...availability];
    const lastRange = newAvailability[dayIndex].timeRanges[newAvailability[dayIndex].timeRanges.length - 1];
    
    // Default to 9:00-10:00, or continue from last range
    const defaultStart = lastRange ? lastRange.end_time : "09:00:00";
    const startHour = parseInt(defaultStart.split(":")[0]);
    const defaultEnd = `${(startHour + 1).toString().padStart(2, "0")}:00:00`;
    
    newAvailability[dayIndex].timeRanges.push({
      start_time: defaultStart,
      end_time: defaultEnd,
    });
    
    setAvailability(newAvailability);
  };

  const removeTimeRange = async (dayIndex: number, rangeIndex: number) => {
    const range = availability[dayIndex].timeRanges[rangeIndex];
    
    // If it has an ID, delete from database
    if (range.id) {
      const { error } = await (supabase
        .from("mentor_weekly_availability" as any)
        .delete()
        .eq("id", range.id) as any);

      if (error) {
        toast({
          title: "Error removing time slot",
          description: error.message,
          variant: "destructive",
        });
        return;
      }
    }

    const newAvailability = [...availability];
    newAvailability[dayIndex].timeRanges.splice(rangeIndex, 1);
    setAvailability(newAvailability);
  };

  const updateTimeRange = (dayIndex: number, rangeIndex: number, field: "start_time" | "end_time", value: string) => {
    const newAvailability = [...availability];
    newAvailability[dayIndex].timeRanges[rangeIndex][field] = value;
    setAvailability(newAvailability);
  };

  const copyToDay = (targetDayIndex: number) => {
    if (copyFromDay === null) return;
    
    const sourceRanges = availability[copyFromDay].timeRanges;
    const newAvailability = [...availability];
    newAvailability[targetDayIndex].timeRanges = sourceRanges.map(r => ({
      start_time: r.start_time,
      end_time: r.end_time,
    }));
    
    setAvailability(newAvailability);
    setCopyFromDay(null);
    
    toast({
      title: "Schedule copied",
      description: `Copied ${DAYS_OF_WEEK[copyFromDay].name}'s schedule to ${DAYS_OF_WEEK[targetDayIndex].name}`,
    });
  };

  const saveAvailability = async () => {
    setSaving(true);
    
    try {
      // Delete all existing availability for this mentor
      await (supabase
        .from("mentor_weekly_availability" as any)
        .delete()
        .eq("mentor_id", mentorId) as any);

      // Insert all new availability
      const inserts: any[] = [];
      availability.forEach(day => {
        day.timeRanges.forEach(range => {
          if (range.start_time && range.end_time) {
            inserts.push({
              mentor_id: mentorId,
              day_of_week: day.day,
              start_time: range.start_time,
              end_time: range.end_time,
              is_active: true,
            });
          }
        });
      });

      if (inserts.length > 0) {
        const { error } = await (supabase
          .from("mentor_weekly_availability" as any)
          .insert(inserts) as any);

        if (error) throw error;
      }

      toast({
        title: "Availability saved",
        description: "Your weekly schedule has been updated successfully",
      });

      onUpdate?.();
      loadAvailability(); // Reload to get new IDs
    } catch (error: any) {
      toast({
        title: "Error saving availability",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const getTotalHours = () => {
    let total = 0;
    availability.forEach(day => {
      day.timeRanges.forEach(range => {
        const start = parseInt(range.start_time?.split(":")[0] || "0");
        const end = parseInt(range.end_time?.split(":")[0] || "0");
        total += Math.max(0, end - start);
      });
    });
    return total;
  };

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
      <CardHeader className="p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="text-lg sm:text-xl flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Weekly Schedule
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              Set your recurring availability. Sessions are 1 hour each.
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-sm">
              {getTotalHours()} hours/week
            </Badge>
            <Button onClick={saveAvailability} disabled={saving}>
              {saving ? "Saving..." : "Save Schedule"}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 space-y-4">
        {availability.map((day, dayIndex) => (
          <div
            key={day.day}
            className="border rounded-lg p-4 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="font-medium text-sm sm:text-base w-24">
                  {day.dayName}
                </span>
                {day.timeRanges.length === 0 && (
                  <Badge variant="secondary" className="text-xs">Unavailable</Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {copyFromDay !== null && copyFromDay !== dayIndex && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToDay(dayIndex)}
                    className="text-xs"
                  >
                    <Check className="h-3 w-3 mr-1" />
                    Paste here
                  </Button>
                )}
                {day.timeRanges.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCopyFromDay(copyFromDay === dayIndex ? null : dayIndex)}
                    className="text-xs"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    {copyFromDay === dayIndex ? "Cancel" : "Copy"}
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => addTimeRange(dayIndex)}
                  className="text-xs"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Time
                </Button>
              </div>
            </div>

            {day.timeRanges.length > 0 && (
              <div className="space-y-2 pl-0 sm:pl-4">
                {day.timeRanges.map((range, rangeIndex) => (
                  <div key={rangeIndex} className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                    <Clock className="h-4 w-4 text-muted-foreground hidden sm:block" />
                    <Select
                      value={range.start_time}
                      onValueChange={(value) => updateTimeRange(dayIndex, rangeIndex, "start_time", value)}
                    >
                      <SelectTrigger className="w-24 sm:w-28 h-9">
                        <SelectValue placeholder="Start" />
                      </SelectTrigger>
                      <SelectContent>
                        {TIME_OPTIONS.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <span className="text-muted-foreground">to</span>
                    <Select
                      value={range.end_time}
                      onValueChange={(value) => updateTimeRange(dayIndex, rangeIndex, "end_time", value)}
                    >
                      <SelectTrigger className="w-24 sm:w-28 h-9">
                        <SelectValue placeholder="End" />
                      </SelectTrigger>
                      <SelectContent>
                        {TIME_OPTIONS.filter(opt => opt.value > range.start_time).map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeTimeRange(dayIndex, rangeIndex)}
                      className="h-9 w-9 p-0"
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                    <Badge variant="outline" className="text-xs ml-auto">
                      {parseInt(range.end_time?.split(":")[0] || "0") - parseInt(range.start_time?.split(":")[0] || "0")}h
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Quick templates */}
        <div className="border-t pt-4 mt-4">
          <p className="text-sm text-muted-foreground mb-3">Quick templates:</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const workdays = [1, 2, 3, 4, 5]; // Mon-Fri
                const newAvailability = [...availability];
                workdays.forEach(day => {
                  newAvailability[day].timeRanges = [
                    { start_time: "09:00:00", end_time: "12:00:00" },
                    { start_time: "14:00:00", end_time: "17:00:00" },
                  ];
                });
                setAvailability(newAvailability);
              }}
            >
              Weekdays 9-12, 2-5
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const workdays = [1, 2, 3, 4, 5];
                const newAvailability = [...availability];
                workdays.forEach(day => {
                  newAvailability[day].timeRanges = [
                    { start_time: "09:00:00", end_time: "17:00:00" },
                  ];
                });
                setAvailability(newAvailability);
              }}
            >
              Weekdays 9-5
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const newAvailability = availability.map(day => ({
                  ...day,
                  timeRanges: [],
                }));
                setAvailability(newAvailability);
              }}
            >
              Clear All
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default WeeklyAvailabilityEditor;
