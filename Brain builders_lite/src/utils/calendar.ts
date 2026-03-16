/**
 * Generate ICS file content for a session/booking.
 */
export function generateICS(params: {
  title: string;
  description: string;
  startDate: string;
  startTime: string;
  durationMinutes?: number;
  attendeeEmail?: string;
}): string {
  const duration = params.durationMinutes ?? 60;
  const [hours, minutes] = params.startTime.split(":").map(Number);
  const start = new Date(params.startDate);
  start.setHours(hours, minutes ?? 0, 0, 0);
  const end = new Date(start.getTime() + duration * 60 * 1000);

  const formatDate = (d: Date) =>
    d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  return `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Brain Bulders//Booking//EN
BEGIN:VEVENT
UID:${Date.now()}-${Math.random().toString(36).slice(2)}@g-creators.com
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(start)}
DTEND:${formatDate(end)}
SUMMARY:${(params.title || "Session").replace(/\n/g, "\\n")}
DESCRIPTION:${(params.description || "").replace(/\n/g, "\\n")}
${params.attendeeEmail ? `ATTENDEE:mailto:${params.attendeeEmail}` : ""}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`;
}

/**
 * Open "Add to Google Calendar" in a new tab.
 * startDate: YYYY-MM-DD, startTime: HH:mm or HH:mm:ss
 */
export function getGoogleCalendarUrl(params: {
  title: string;
  description?: string;
  startDate: string;
  startTime: string;
  durationMinutes?: number;
}): string {
  const duration = params.durationMinutes ?? 60;
  const [hours, minutes] = params.startTime.split(":").map(Number);
  const start = new Date(params.startDate);
  start.setHours(hours, minutes ?? 0, 0, 0);
  const end = new Date(start.getTime() + duration * 60 * 1000);

  const format = (d: Date) =>
    d.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  const params_ = new URLSearchParams({
    action: "TEMPLATE",
    text: params.title || "Session",
    dates: `${format(start)}/${format(end)}`,
  });
  if (params.description) {
    params_.set("details", params.description);
  }
  return `https://calendar.google.com/calendar/render?${params_.toString()}`;
}
