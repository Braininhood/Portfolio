import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, Clock, DollarSign, Edit } from "lucide-react";
import type { MentorBooking } from "./MentorSessionEditDialog";

interface MentorBookingsCardProps {
  bookings: MentorBooking[];
  type: "upcoming" | "past";
  onEditClick?: (booking: MentorBooking) => void;
}

export const MentorBookingsCard = ({ bookings, type, onEditClick }: MentorBookingsCardProps) => {
  const title = type === "upcoming" ? "Upcoming Sessions" : "Past Sessions";
  const description = type === "upcoming" 
    ? "Your scheduled mentorship sessions with students" 
    : "Your session history";

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6">
        <CardTitle className="text-lg sm:text-xl">{title}</CardTitle>
        <CardDescription className="text-sm">{description}</CardDescription>
      </CardHeader>
      <CardContent className="p-4 sm:p-6 pt-0 sm:pt-0">
        {bookings.length === 0 ? (
          <p className="text-center py-6 sm:py-8 text-muted-foreground text-sm">
            No {type} sessions
          </p>
        ) : (
          <div className="space-y-3 sm:space-y-4">
            {bookings.map((booking) => (
              <div
                key={booking.id}
                className={`flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 border rounded-lg gap-3 ${
                  type === "past" ? "opacity-60" : ""
                }`}
              >
                <div className="space-y-2 sm:space-y-1 flex-1 min-w-0">
                  <div className="flex items-center justify-between sm:justify-start gap-2">
                    <p className="font-semibold text-sm sm:text-base truncate">{booking.user_email}</p>
                    <Badge variant={type === "past" ? "secondary" : "default"} className="sm:hidden shrink-0">
                      {booking.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-2 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                      {new Date(booking.booking_date).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                      {booking.booking_time}
                    </span>
                    <span className="flex items-center gap-1">
                      <DollarSign className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                      ${String(booking.price).replace(/^\$/, "").trim()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={type === "past" ? "secondary" : "default"} className="hidden sm:inline-flex">
                    {booking.status}
                  </Badge>
                  {type === "upcoming" && onEditClick && (
                    <Button variant="ghost" size="sm" onClick={() => onEditClick(booking)} title="Edit session">
                      <Edit className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
