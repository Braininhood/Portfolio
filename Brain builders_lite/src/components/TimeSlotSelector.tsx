import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from "lucide-react";

/** Minimal slot shape; extend this so parent and selector share the same slot type */
export interface BaseTimeSlot {
  id: string;
  date: string;
  time: string;
  mentor_id?: string;
  mentorId?: string;
  is_available?: boolean;
  available?: boolean;
}

interface TimeSlotSelectorProps<T extends BaseTimeSlot = BaseTimeSlot> {
  timeSlots: T[];
  onSelectSlot: (slot: T) => void;
}

function TimeSlotSelector<T extends BaseTimeSlot>({ timeSlots, onSelectSlot }: TimeSlotSelectorProps<T>) {
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [currentWeekStart, setCurrentWeekStart] = useState(new Date());

  // Get unique dates
  const uniqueDates = useMemo(() => {
    const dates = [...new Set(timeSlots.map(slot => slot.date))].sort();
    return dates;
  }, [timeSlots]);

  // Get week dates
  const weekDates = useMemo(() => {
    const dates: Date[] = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(currentWeekStart);
      date.setDate(currentWeekStart.getDate() + i);
      dates.push(date);
    }
    return dates;
  }, [currentWeekStart]);

  // Filter slots by selected date
  const slotsForDate = useMemo(() => {
    if (!selectedDate) return [];
    return timeSlots.filter(slot => slot.date === selectedDate);
  }, [selectedDate, timeSlots]);

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minutes} ${period}`;
  };

  const nextWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() + 7);
    setCurrentWeekStart(newDate);
    setSelectedDate("");
  };

  const prevWeek = () => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() - 7);
    if (newDate >= new Date()) {
      setCurrentWeekStart(newDate);
      setSelectedDate("");
    }
  };

  return (
    <div className="space-y-6">
      {/* Week Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={prevWeek}
          disabled={currentWeekStart <= new Date()}
        >
          <ChevronLeft size={16} />
          Previous
        </Button>
        <div className="flex items-center gap-2 text-muted-foreground">
          <CalendarIcon size={16} />
          <span className="text-sm font-medium">
            {weekDates[0].toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={nextWeek}>
          Next
          <ChevronRight size={16} />
        </Button>
      </div>

      {/* Date Selector */}
      <div className="grid grid-cols-7 gap-2">
        {weekDates.map((date, idx) => {
          const dateStr = date.toISOString().split('T')[0];
          const hasSlots = uniqueDates.includes(dateStr);
          const isSelected = selectedDate === dateStr;
          const isPast = date < new Date();

          return (
            <button
              key={idx}
              onClick={() => hasSlots && !isPast && setSelectedDate(dateStr)}
              disabled={!hasSlots || isPast}
              className={`p-3 rounded-lg border text-center transition-all duration-300 ${
                isSelected
                  ? "bg-accent text-accent-foreground border-accent shadow-medium"
                  : hasSlots && !isPast
                  ? "border-border hover:border-accent hover:shadow-subtle"
                  : "border-border opacity-50 cursor-not-allowed"
              }`}
            >
              <div className="text-xs text-muted-foreground mb-1">
                {date.toLocaleDateString('en-US', { weekday: 'short' })}
              </div>
              <div className="text-lg font-semibold">
                {date.getDate()}
              </div>
            </button>
          );
        })}
      </div>

      {/* Time Slots */}
      {selectedDate && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">
              Available times for {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h3>
            
            {slotsForDate.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {slotsForDate.map((slot) => {
                  const isAvailable = slot.is_available ?? slot.available ?? false;
                  return (
                    <Button
                      key={slot.id}
                      variant={isAvailable ? "outline" : "ghost"}
                      disabled={!isAvailable}
                      onClick={() => isAvailable && onSelectSlot(slot)}
                      className={`${
                        isAvailable
                          ? "hover:bg-accent hover:text-accent-foreground"
                          : "opacity-50 cursor-not-allowed"
                      }`}
                    >
                      {formatTime(slot.time)}
                    </Button>
                  );
                })}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-4">
                No available time slots for this date
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {!selectedDate && (
        <Card>
          <CardContent className="p-12 text-center">
            <CalendarIcon className="mx-auto mb-4 text-muted-foreground" size={48} />
            <p className="text-muted-foreground">
              Select a date to view available time slots
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TimeSlotSelector;