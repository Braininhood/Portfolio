// @ts-ignore - Deno imports work at runtime
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
// @ts-ignore - Deno imports work at runtime
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const GOOGLE_CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
const GOOGLE_CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

async function refreshAccessToken(refreshToken: string): Promise<{ access_token: string; expires_in: number } | null> {
  try {
    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID!,
        client_secret: GOOGLE_CLIENT_SECRET!,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      }),
    });

    const data = await response.json();
    if (data.error) {
      console.error("Token refresh error:", data);
      return null;
    }
    return data;
  } catch (error) {
    console.error("Failed to refresh token:", error);
    return null;
  }
}

async function addEventToCalendar(
  accessToken: string,
  calendarId: string,
  event: {
    summary: string;
    description: string;
    start: { dateTime: string; timeZone: string };
    end: { dateTime: string; timeZone: string };
    attendees?: Array<{ email: string }>;
    reminders?: {
      useDefault: boolean;
      overrides?: Array<{ method: string; minutes: number }>;
    };
  }
) {
  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(event),
    }
  );

  const data = await response.json();
  
  if (data.error) {
    throw new Error(data.error.message || "Failed to add calendar event");
  }

  return data;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log("[ADD-CALENDAR-EVENT] Request received");
    
    const {
      mentorId,
      learnerId,
      bookingId,
      title,
      description,
      startDate,
      startTime,
      duration,
      timeZone = "UTC",
    } = await req.json();

    console.log("[ADD-CALENDAR-EVENT] Params:", { mentorId, learnerId, bookingId, title, startDate, startTime });

    if (!mentorId || !bookingId || !title || !startDate || !startTime) {
      throw new Error("Missing required parameters");
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Parse date and time
    const [hours, minutes] = startTime.split(":");
    const start = new Date(`${startDate}T${hours}:${minutes}:00`);
    const end = new Date(start.getTime() + (duration || 60) * 60 * 1000);

    const eventData = {
      summary: title,
      description: description || "",
      start: {
        dateTime: start.toISOString(),
        timeZone,
      },
      end: {
        dateTime: end.toISOString(),
        timeZone,
      },
      reminders: {
        useDefault: false,
        overrides: [
          { method: "email", minutes: 24 * 60 }, // 24 hours before
          { method: "popup", minutes: 60 }, // 1 hour before
        ],
      },
    };

    const results = {
      mentorEventAdded: false,
      learnerEventAdded: false,
      mentorEventId: null as string | null,
      learnerEventId: null as string | null,
    };

    // Add event to mentor's calendar
    console.log("[ADD-CALENDAR-EVENT] Checking mentor calendar connection...");
    const { data: mentorConnection } = await supabase
      .from("mentor_calendar_connections")
      .select("*")
      .eq("mentor_id", mentorId)
      .single();

    if (mentorConnection && mentorConnection.sync_enabled) {
      console.log("[ADD-CALENDAR-EVENT] Adding event to mentor's calendar...");
      
      let accessToken = mentorConnection.access_token;
      const tokenExpiry = new Date(mentorConnection.token_expires_at);
      
      // Refresh token if expired
      if (tokenExpiry < new Date()) {
        const newTokens = await refreshAccessToken(mentorConnection.refresh_token);
        if (newTokens) {
          accessToken = newTokens.access_token;
          await supabase
            .from("mentor_calendar_connections")
            .update({
              access_token: accessToken,
              token_expires_at: new Date(Date.now() + newTokens.expires_in * 1000).toISOString(),
            })
            .eq("mentor_id", mentorId);
        }
      }

      try {
        const calendarId = mentorConnection.calendar_id || "primary";
        const mentorEvent = await addEventToCalendar(accessToken, calendarId, eventData);
        results.mentorEventAdded = true;
        results.mentorEventId = mentorEvent.id;
        console.log("[ADD-CALENDAR-EVENT] Mentor event added:", mentorEvent.id);
      } catch (error) {
        console.error("[ADD-CALENDAR-EVENT] Failed to add mentor event:", error);
      }
    }

    // TODO: Add event to learner's calendar if they have connected one
    // This would require a similar calendar_connections table for learners
    // For now, they will receive ICS file via email

    // Store calendar event IDs in the booking record
    if (results.mentorEventId) {
      await supabase
        .from("bookings")
        .update({
          mentor_calendar_event_id: results.mentorEventId,
        })
        .eq("id", bookingId);
    }

    console.log("[ADD-CALENDAR-EVENT] Success!");
    
    return new Response(
      JSON.stringify({
        success: true,
        ...results,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error: unknown) {
    console.error("[ADD-CALENDAR-EVENT] Error:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
