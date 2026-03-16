/**
 * Timezone utilities: profile timezone storage and conversion for bookings/availability.
 * Bookings are stored in mentor's timezone. Display: mentor sees as-is, learner sees converted to learner TZ.
 */

const DEFAULT_TZ = "UTC";

/** Common IANA timezones for selector, grouped by region */
export const TIMEZONE_OPTIONS: { value: string; label: string; region: string }[] = (() => {
  const zones = [
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Europe/Moscow",
    "Europe/Kyiv",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Vancouver",
    "America/Sao_Paulo",
    "America/Buenos_Aires",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Singapore",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Pacific/Auckland",
    "UTC",
  ];
  const regionOrder: Record<string, string> = {
    Europe: "Europe",
    America: "Americas",
    Asia: "Asia",
    Australia: "Australia",
    Pacific: "Pacific",
    UTC: "UTC",
  };
  return zones.map((value) => {
    const region = value.startsWith("Europe")
      ? "Europe"
      : value.startsWith("America")
        ? "Americas"
        : value.startsWith("Asia")
          ? "Asia"
          : value.startsWith("Australia")
            ? "Australia"
            : value.startsWith("Pacific")
              ? "Pacific"
              : "UTC";
    let label = value;
    try {
      const formatter = new Intl.DateTimeFormat("en", {
        timeZone: value,
        timeZoneName: "long",
      });
      const parts = formatter.formatToParts(new Date());
      const tzPart = parts.find((p) => p.type === "timeZoneName");
      label = tzPart ? `${value} (${tzPart.value})` : value;
    } catch {
      label = value;
    }
    return { value, label, region: regionOrder[region] || region };
  });
})();

/** Get user's timezone for display (profile or mentor_profile). Prefer mentor TZ for mentor, else profile. */
export function getEffectiveTimezone(
  profileTimezone: string | null | undefined,
  mentorTimezone: string | null | undefined,
  isMentor: boolean
): string {
  if (isMentor && mentorTimezone) return mentorTimezone;
  if (profileTimezone) return profileTimezone;
  return DEFAULT_TZ;
}

/**
 * Parse date (YYYY-MM-DD) and time (HH:mm or HH:mm:ss) as local in the given timezone; return as Date (UTC).
 * Uses binary search over the day so DST is respected.
 */
export function parseInTimezone(
  dateStr: string,
  timeStr: string,
  timezone: string
): Date {
  const datePart = dateStr.trim().split("T")[0];
  const [y, mo, d] = datePart.split("-").map(Number);
  const [h = 0, m = 0, s = 0] = timeStr.trim().split(":").map(Number);
  const targetDate = datePart;
  const targetTime = `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;

  const dayStartUtc = Date.UTC(y, mo - 1, d, 0, 0, 0, 0);
  const dayEndUtc = Date.UTC(y, mo - 1, d + 1, 0, 0, 0, 0);
  let low = dayStartUtc - 24 * 60 * 60 * 1000;
  let high = dayEndUtc + 24 * 60 * 60 * 1000;

  for (let i = 0; i < 50; i++) {
    const mid = Math.floor((low + high) / 2);
    const f = formatInTimezone(new Date(mid), timezone);
    const cmp = f.date.localeCompare(targetDate) || f.time.localeCompare(targetTime);
    if (cmp === 0) return new Date(mid);
    if (cmp < 0) low = mid;
    else high = mid;
  }
  return new Date((low + high) / 2);
}

/**
 * Format a Date in the given timezone as { date: YYYY-MM-DD, time: HH:mm:ss }.
 */
export function formatInTimezone(
  date: Date,
  timezone: string
): { date: string; time: string } {
  try {
    const formatter = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
    const parts = formatter.formatToParts(date);
    const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
    const dateStr = `${get("year")}-${get("month")}-${get("day")}`;
    const timeStr = `${get("hour")}:${get("minute")}:${get("second")}`;
    return { date: dateStr, time: timeStr };
  } catch {
    const dateStr = date.toISOString().split("T")[0];
    const timeStr = date.toISOString().split("T")[1].slice(0, 8);
    return { date: dateStr, time: timeStr };
  }
}

/**
 * Convert a date+time from one timezone to another.
 * fromDate/fromTime are in fromTz; returns { date, time } in toTz.
 */
export function convertDateTime(
  fromDate: string,
  fromTime: string,
  fromTz: string,
  toTz: string
): { date: string; time: string } {
  const utcDate = parseInTimezone(fromDate, fromTime, fromTz);
  return formatInTimezone(utcDate, toTz);
}

/**
 * Format booking date/time for display in the user's timezone.
 * If viewerTz equals storageTz (e.g. mentor viewing), returns same date/time.
 */
export function formatBookingInTimezone(
  bookingDate: string,
  bookingTime: string,
  storageTz: string,
  viewerTz: string
): { date: string; time: string } {
  if (!storageTz) return { date: bookingDate, time: bookingTime };
  if (storageTz === viewerTz || !viewerTz) return { date: bookingDate, time: bookingTime };
  return convertDateTime(bookingDate, bookingTime, storageTz, viewerTz);
}
